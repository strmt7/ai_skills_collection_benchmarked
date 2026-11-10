// Bounded native extraction of exact, admitted vendor cabinets.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;

namespace SkillsBootstrap {
public static class NativeCabinet {
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
    struct FileInCabinet {
        public IntPtr Name;
        public uint Size, Error;
        public ushort Date, Time, Attributes;
        [MarshalAs(UnmanagedType.ByValTStr,SizeConst=260)] public string Target;
    }
    [UnmanagedFunctionPointer(CallingConvention.Winapi)]
    delegate uint Callback(IntPtr context,uint notification,UIntPtr first,UIntPtr second);
    [DllImport("setupapi.dll",CharSet=CharSet.Unicode,SetLastError=true)]
    static extern bool SetupIterateCabinetW(string cabinet,uint reserved,Callback callback,IntPtr context);
    public sealed class Entry {
        public string name;
        public uint bytes, attributes;
    }
    static void Ordinary(string path) {
        string current=Path.GetFullPath(path);
        while(!String.IsNullOrEmpty(current)) {
            if((File.Exists(current) || Directory.Exists(current)) && (File.GetAttributes(current)&FileAttributes.ReparsePoint)!=0)
                throw new InvalidDataException("Native extraction must not traverse a link or junction");
            current=Path.GetDirectoryName(current);
        }
    }
    public static Entry[] Read(string cabinet,string output,bool extract) {
        Ordinary(cabinet);
        Ordinary(output);
        if(extract) {
            output=Path.GetFullPath(output);
            if(Directory.Exists(output) || File.Exists(output)) throw new IOException("Select a fresh output directory");
            Directory.CreateDirectory(output);
        }
        var entries=new List<Entry>();
        var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        string failure=null;
        long bytes=0;
        Callback callback=delegate(IntPtr context,uint notification,UIntPtr first,UIntPtr second) {
            try {
                if(notification==0x12) throw new InvalidDataException("Split cabinets are outside the qualified payload");
                if(notification!=0x11) return 0;
                IntPtr pointer=new IntPtr(unchecked((long)first.ToUInt64()));
                var item=(FileInCabinet)Marshal.PtrToStructure(pointer,typeof(FileInCabinet));
                string name=Marshal.PtrToStringUni(item.Name);
                if(String.IsNullOrEmpty(name) || name!=Path.GetFileName(name) || name=="." || name==".." ||
                    name.IndexOfAny(new[]{':','\\','/'})>=0 || name.EndsWith(".") || name.EndsWith(" ") || !seen.Add(name))
                    throw new InvalidDataException("Noncanonical cabinet member");
                string device=Path.GetFileNameWithoutExtension(name).ToUpperInvariant();
                if(device=="CON" || device=="PRN" || device=="AUX" || device=="NUL" ||
                    (device.Length==4 && (device.StartsWith("COM") || device.StartsWith("LPT")) && device[3]>='0' && device[3]<='9'))
                    throw new InvalidDataException("Device names are not extraction targets");
                bytes+=item.Size;
                if(item.Error!=0 || item.Size>33554432 || bytes>134217728 || entries.Count>=2048 || (item.Attributes&0x410)!=0)
                    throw new InvalidDataException("Cabinet member exceeds its declared payload bounds");
                entries.Add(new Entry {name=name,bytes=item.Size,attributes=item.Attributes});
                if(!extract) return 2; // FILEOP_SKIP
                string target=Path.Combine(output,name);
                if(target.Length>=260 || File.Exists(target) || Directory.Exists(target))
                    throw new InvalidDataException("The native cabinet target is unavailable");
                var characters=new char[260];
                target.CopyTo(0,characters,0,target.Length);
                Marshal.Copy(characters,0,IntPtr.Add(pointer,(int)Marshal.OffsetOf(typeof(FileInCabinet),"Target")),260);
                return 1; // FILEOP_DOIT
            } catch(Exception error) { failure=error.ToString(); return 0; }
        };
        bool success=SetupIterateCabinetW(cabinet,0,callback,IntPtr.Zero);
        int nativeError=Marshal.GetLastWin32Error();
        GC.KeepAlive(callback);
        if(failure!=null) throw new InvalidDataException(failure);
        if(!success) throw new Win32Exception(nativeError);
        if(extract) {
            foreach(var entry in entries) {
                var file=new FileInfo(Path.Combine(output,entry.name));
                if(!file.Exists || file.Length!=entry.bytes || (file.Attributes&FileAttributes.ReparsePoint)!=0)
                    throw new InvalidDataException("Native extraction differs from its inventory");
            }
            if(Directory.GetFileSystemEntries(output).Length!=entries.Count)
                throw new InvalidDataException("Unexpected native extraction resource");
        }
        return entries.ToArray();
    }
}

}
