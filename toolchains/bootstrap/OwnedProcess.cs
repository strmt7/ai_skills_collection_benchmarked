// Native bootstrap supervision before a Python interpreter exists.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

namespace SkillsBootstrap {
    public static class OwnedProcess {
        [StructLayout(LayoutKind.Sequential)] struct Security {
            public int Length; public IntPtr Descriptor; public int Inherit;
        }
        [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Startup {
            public int Size; public string Reserved, Desktop, Title;
            public uint X,Y,XSize,YSize,XChars,YChars,Fill,Flags;
            public short Show, ReservedBytes; public IntPtr ReservedPointer, Input, Output, Error;
        }
        [StructLayout(LayoutKind.Sequential)] struct ExtendedStartup {
            public Startup Startup; public IntPtr Attributes;
        }
        [StructLayout(LayoutKind.Sequential)] struct ProcessInfo {
            public IntPtr Process, Thread; public uint ProcessId, ThreadId;
        }
        [StructLayout(LayoutKind.Sequential)] struct BasicLimits {
            public long ProcessTime, JobTime; public uint Flags;
            public UIntPtr Minimum, Maximum; public uint Processes;
            public UIntPtr Affinity; public uint Priority, Scheduling;
        }
        [StructLayout(LayoutKind.Sequential)] struct Limits {
            public BasicLimits Basic;
            public ulong ReadOperations,WriteOperations,OtherOperations,ReadBytes,WriteBytes,OtherBytes;
            public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory;
        }
        [StructLayout(LayoutKind.Sequential)] struct Accounting {
            public long User, Kernel, PeriodUser, PeriodKernel;
            public uint Faults, Total, Active, Terminated;
        }
        [DllImport("kernel32",SetLastError=true)] static extern IntPtr CreateJobObjectW(IntPtr attributes,IntPtr name);
        [DllImport("kernel32",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int kind,ref Limits limits,int length);
        [DllImport("kernel32",SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr job,int kind,out Accounting data,int length,IntPtr returned);
        [DllImport("kernel32",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
        [DllImport("kernel32",SetLastError=true)] static extern bool IsProcessInJob(IntPtr process,IntPtr job,out bool inside);
        [DllImport("kernel32",SetLastError=true)] static extern bool TerminateJobObject(IntPtr job,uint code);
        [DllImport("kernel32",SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint code);
        [DllImport("kernel32",SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
        [DllImport("kernel32",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
        [DllImport("kernel32",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle,uint milliseconds);
        [DllImport("kernel32",SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process,out uint code);
        [DllImport("kernel32",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateFileW(string path,uint access,uint share,ref Security security,uint creation,uint attributes,IntPtr template);
        [DllImport("kernel32",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcessW(string app,StringBuilder command,IntPtr processAttributes,IntPtr threadAttributes,bool inherit,uint flags,IntPtr environment,string cwd,ref ExtendedStartup startup,out ProcessInfo process);
        [DllImport("kernel32",SetLastError=true)] static extern bool InitializeProcThreadAttributeList(IntPtr list,int count,uint flags,ref IntPtr bytes);
        [DllImport("kernel32",SetLastError=true)] static extern bool UpdateProcThreadAttribute(IntPtr list,uint flags,IntPtr attribute,IntPtr value,IntPtr bytes,IntPtr previous,IntPtr returned);
        [DllImport("kernel32")] static extern void DeleteProcThreadAttributeList(IntPtr list);

        static void Require(bool condition) { if(!condition) throw new Win32Exception(Marshal.GetLastWin32Error()); }
        static string NativePath(string path) {
            string full=Path.GetFullPath(path);
            if(full.StartsWith(@"\\?\",StringComparison.Ordinal)) return full;
            if(full.Length<260) return full;
            return full.StartsWith(@"\\",StringComparison.Ordinal) ? @"\\?\UNC\"+full.Substring(2) : @"\\?\"+full;
        }
        static string Quote(string value) {
            if(value==null || value.IndexOf('\0')>=0) throw new ArgumentException("Invalid argument");
            var result=new StringBuilder("\""); int slashes=0;
            foreach(char c in value) {
                if(c=='\\') { slashes++; continue; }
                result.Append('\\',c=='"' ? slashes*2+1 : slashes); slashes=0; result.Append(c);
            }
            return result.Append('\\',slashes*2).Append('"').ToString();
        }
        static long OutputSize(string stdout,string stderr) {
            return new FileInfo(stdout).Length+new FileInfo(stderr).Length;
        }
        public sealed class Result {
            public uint exit_code, active_processes_after_cleanup;
            public string termination_reason;
            public bool windows_job=true, assigned_before_resume=true, kill_on_close=true, explicit_environment=true, attested_while_suspended=true;
            public double elapsed_seconds;
            public long observed_output_bytes, retained_output_bytes;
        }
        public static Result Run(string executable,string[] arguments,string cwd,
            Dictionary<string,string> environment,string stdout,string stderr,
            int timeoutSeconds,long outputLimit,long memoryLimit,int processLimit) {
            if(timeoutSeconds<=0 || outputLimit<=0 || memoryLimit<=0 || processLimit<=0)
                throw new ArgumentException("Positive process budgets are required");
            executable=NativePath(executable); cwd=NativePath(cwd);
            stdout=NativePath(stdout); stderr=NativePath(stderr);
            IntPtr job=IntPtr.Zero,input=IntPtr.Zero,output=IntPtr.Zero,error=IntPtr.Zero;
            IntPtr environmentBlock=IntPtr.Zero,attributes=IntPtr.Zero,handles=IntPtr.Zero;
            ProcessInfo process=new ProcessInfo(); bool initialized=false,assigned=false;
            var result=new Result(); var clock=Stopwatch.StartNew();
            try {
                job=CreateJobObjectW(IntPtr.Zero,IntPtr.Zero); Require(job!=IntPtr.Zero);
                var limits=new Limits(); limits.Basic.Flags=0x2000|0x200|0x8;
                limits.Basic.Processes=(uint)processLimit; limits.JobMemory=(UIntPtr)(ulong)memoryLimit;
                Require(SetInformationJobObject(job,9,ref limits,Marshal.SizeOf(typeof(Limits))));
                var security=new Security {Length=Marshal.SizeOf(typeof(Security)),Inherit=1};
                input=CreateFileW("NUL",0x80000000,1,ref security,3,0,IntPtr.Zero);
                output=CreateFileW(stdout,0x40000000,1,ref security,1,0x80,IntPtr.Zero);
                error=CreateFileW(stderr,0x40000000,1,ref security,1,0x80,IntPtr.Zero);
                Require(input!=IntPtr.Zero && output!=IntPtr.Zero && error!=IntPtr.Zero && input!=new IntPtr(-1) && output!=new IntPtr(-1) && error!=new IntPtr(-1));
                IntPtr bytes=IntPtr.Zero;
                InitializeProcThreadAttributeList(IntPtr.Zero,1,0,ref bytes);
                Require(bytes!=IntPtr.Zero); attributes=Marshal.AllocHGlobal(bytes);
                Require(InitializeProcThreadAttributeList(attributes,1,0,ref bytes)); initialized=true;
                handles=Marshal.AllocHGlobal(IntPtr.Size*3);
                Marshal.WriteIntPtr(handles,0,input); Marshal.WriteIntPtr(handles,IntPtr.Size,output); Marshal.WriteIntPtr(handles,IntPtr.Size*2,error);
                Require(UpdateProcThreadAttribute(attributes,0,new IntPtr(0x20002),handles,new IntPtr(IntPtr.Size*3),IntPtr.Zero,IntPtr.Zero));
                var startup=new ExtendedStartup(); startup.Startup.Size=Marshal.SizeOf(typeof(ExtendedStartup));
                startup.Startup.Flags=0x100; startup.Startup.Input=input; startup.Startup.Output=output; startup.Startup.Error=error; startup.Attributes=attributes;
                var env=new StringBuilder(); var keys=new List<string>(environment.Keys); keys.Sort(StringComparer.OrdinalIgnoreCase);
                foreach(string key in keys) {
                    string value=environment[key];
                    if(key.Length==0 || key.IndexOfAny(new[]{'\0','='})>=0 || value==null || value.IndexOf('\0')>=0) throw new ArgumentException("Invalid environment");
                    env.Append(key).Append('=').Append(value).Append('\0');
                }
                env.Append('\0'); environmentBlock=Marshal.StringToHGlobalUni(env.ToString());
                var command=new StringBuilder(Quote(executable));
                foreach(string argument in arguments) command.Append(' ').Append(Quote(argument));
                Require(CreateProcessW(executable,command,IntPtr.Zero,IntPtr.Zero,true,0x08000000|0x80000|0x400|0x4,environmentBlock,cwd,ref startup,out process));
                Require(AssignProcessToJobObject(job,process.Process)); assigned=true;
                bool inside; Require(IsProcessInJob(process.Process,job,out inside));
                if(!inside) throw new InvalidOperationException("Process did not enter its owning job");
                Require(ResumeThread(process.Thread)!=0xffffffff);
                while(true) {
                    uint state=WaitForSingleObject(process.Process,50);
                    if(state==0) break;
                    Require(state==258);
                    if(clock.Elapsed.TotalSeconds>=timeoutSeconds) { result.termination_reason="timeout"; Require(TerminateJobObject(job,124)); break; }
                    if(OutputSize(stdout,stderr)>outputLimit) { result.termination_reason="output_limit"; Require(TerminateJobObject(job,125)); break; }
                }
                Require(WaitForSingleObject(process.Process,5000)==0);
                Require(GetExitCodeProcess(process.Process,out result.exit_code));
                Require(TerminateJobObject(job,0));
                var cleanup=Stopwatch.StartNew(); Accounting accounting;
                do {
                    Require(QueryInformationJobObject(job,1,out accounting,Marshal.SizeOf(typeof(Accounting)),IntPtr.Zero));
                    if(accounting.Active==0) break;
                    Thread.Sleep(20);
                } while(cleanup.Elapsed.TotalSeconds<5);
                result.active_processes_after_cleanup=accounting.Active;
                if(accounting.Active!=0) throw new InvalidOperationException("Owned processes did not terminate");
                Require(CloseHandle(output)); output=IntPtr.Zero;
                Require(CloseHandle(error)); error=IntPtr.Zero;
                result.observed_output_bytes=OutputSize(stdout,stderr);
                if(result.observed_output_bytes>outputLimit) {
                    result.termination_reason="output_limit";
                    long remaining=outputLimit;
                    foreach(string path in new[]{stdout,stderr}) {
                        using(var stream=new FileStream(path,FileMode.Open,FileAccess.Write,FileShare.Read)) {
                            long retained=Math.Min(remaining,stream.Length); stream.SetLength(retained); remaining-=retained;
                        }
                    }
                }
                result.retained_output_bytes=OutputSize(stdout,stderr);
                result.elapsed_seconds=clock.Elapsed.TotalSeconds;
                return result;
            } finally {
                if(process.Process!=IntPtr.Zero) {
                    if(assigned) TerminateJobObject(job,125); else TerminateProcess(process.Process,125);
                }
                foreach(IntPtr handle in new[]{process.Thread,process.Process,input,output,error,job})
                    if(handle!=IntPtr.Zero && handle!=new IntPtr(-1)) CloseHandle(handle);
                if(initialized) DeleteProcThreadAttributeList(attributes);
                foreach(IntPtr pointer in new[]{attributes,handles,environmentBlock}) if(pointer!=IntPtr.Zero) Marshal.FreeHGlobal(pointer);
            }
        }
    }
}
