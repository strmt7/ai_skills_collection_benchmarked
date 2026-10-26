#!/usr/bin/env bash
# Read-only poster preflight. Manual visual and scientific review is required.
set -u
export LC_ALL=C

usage() { printf 'Usage: %s <poster.pdf>\n' "$0"; }
if [ "${1:-}" = --help ] || [ "${1:-}" = -h ]; then
    usage
    exit 0
fi
if [ "$#" -ne 1 ]; then
    usage >&2
    exit 1
fi

file=$1
case "$file" in
    [A-Za-z]:*|\\\\*)
        if command -v cygpath >/dev/null 2>&1; then
            if converted=$(LC_ALL=C.UTF-8 cygpath -u -- "$file"); then
                file=$converted
            else
                printf '[FAIL] Could not convert the Windows path.\n' >&2
                exit 1
            fi
        fi
        ;;
esac
case "$file" in /*) ;; *) file="./$file" ;; esac
if [ ! -f "$file" ] || [ ! -r "$file" ]; then
    printf '[FAIL] The PDF is not a readable regular file: %s\n' "$file" >&2
    exit 1
fi

failed=0
incomplete=0
available() { command -v "$1" >/dev/null 2>&1; }
missing() { printf '[WARN] %s is unavailable; this check is incomplete.\n' "$1"; incomplete=1; }

printf 'Poster preflight\nFile: %s\n' "$file"
if size=$(wc -c < "$file"); then
    size=${size//[[:space:]]/}
    case "$size" in
        ''|*[!0-9]*) printf '[FAIL] Invalid file size.\n' >&2; failed=1 ;;
        *)
            printf '\nFile size: %s bytes\n' "$size"
            if [ "$size" -gt 52428800 ]; then
                printf '[WARN] The file exceeds 50 MiB; verify the submission limit.\n'
            fi
            ;;
    esac
else
    printf '[FAIL] Could not read the file size.\n' >&2
    failed=1
fi

printf '\nPage information:\n'
if available pdfinfo; then
    if info=$(pdfinfo "$file"); then
        if ! printf '%s\n' "$info" | awk '
            /^Pages:/ { pages=$2; page_lines++ }
            /^Page size:/ {
                dimension_lines++
                if ($3 ~ /^[0-9]+([.][0-9]+)?$/ && $4 == "x" && $5 ~ /^[0-9]+([.][0-9]+)?$/ && $3+0>0 && $5+0>0) dimensions=1
                print
            }
            END {
                if (page_lines != 1 || dimension_lines != 1 || pages !~ /^[0-9]+$/ || pages != 1 || !dimensions) {
                    print "[FAIL] Expected one page and readable page dimensions."; exit 1
                }
                print "[OK] One page; compare its dimensions with the venue requirements."
            }'; then
            failed=1
        fi
    else
        printf '[FAIL] pdfinfo could not inspect the PDF.\n'
        failed=1
    fi
else
    missing pdfinfo
fi

printf '\nFont embedding:\n'
if available pdffonts; then
    if fonts=$(pdffonts "$file"); then
        if ! printf '%s\n' "$fonts" | awk '
            NR==1 { if ($0 !~ /emb.*sub.*uni.*object ID/) invalid=1; next }
            NR==2 { if ($0 !~ /^[-[:space:]]+$/) invalid=1; next }
            NR>2 && NF {
                if (NF<8 || ($(NF-4)!="yes" && $(NF-4)!="no")) invalid=1
                else {
                    count++
                    if ($(NF-4)=="no") { unembedded++; print "[FAIL] Unembedded font: " $0 }
                }
            }
            END {
                if (invalid || NR<2) { print "[FAIL] Unrecognized font report."; exit 1 }
                if (unembedded) { print "[FAIL] " unembedded " font(s) are not embedded."; exit 1 }
                if (count) print "[OK] All listed fonts are embedded."
                else print "[INFO] No fonts listed; inspect outlined or rasterized text."
            }'; then
            failed=1
        fi
    else
        printf '[FAIL] pdffonts could not inspect the PDF.\n'
        failed=1
    fi
else
    missing pdffonts
fi

printf '\nRaster image resolution:\n'
if available pdfimages; then
    if images=$(pdfimages -list "$file"); then
        if ! printf '%s\n' "$images" | awk '
            NR==1 { if ($0 !~ /x-ppi.*y-ppi/) invalid=1; next }
            NR==2 { if ($0 !~ /^[-[:space:]]+$/) invalid=1; next }
            NR>2 && NF {
                if (NF<16 || $1 !~ /^[0-9]+$/ || $2 !~ /^[0-9]+$/ || $3 !~ /^(image|mask|smask|stencil)$/) invalid=1
                else if ($3=="image") {
                    if ($13 !~ /^[0-9]+([.][0-9]+)?$/ || $14 !~ /^[0-9]+([.][0-9]+)?$/) invalid=1
                    else {
                        count++
                        if ($13+0<300 || $14+0<300) { low++; print "[WARN] Low-resolution image: " $0 }
                    }
                }
            }
            END {
                if (invalid || NR<2) { print "[FAIL] Unrecognized image report."; exit 1 }
                if (!count) print "[INFO] No raster images listed; inspect vector artwork manually."
                else if (low) print "[WARN] " low " raster image(s) below 300 PPI; check print requirements."
                else print "[OK] Listed raster images are at least 300 PPI."
            }'; then
            failed=1
        fi
    else
        printf '[FAIL] pdfimages could not inspect the PDF.\n'
        failed=1
    fi
else
    missing pdfimages
fi

printf '\nManual review is still required for layout, readability, figures, data, citations and printer requirements.\n'
if [ "$failed" -ne 0 ]; then
    printf '[FAIL] Automated preflight found errors.\n'
    exit 1
fi
if [ "$incomplete" -ne 0 ]; then
    printf '[WARN] Automated preflight is incomplete.\n'
    exit 2
fi
printf '[OK] Automated preflight passed; complete manual review.\n'
