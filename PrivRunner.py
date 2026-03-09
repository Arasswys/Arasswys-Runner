import ctypes
import ctypes.wintypes as wintypes
import subprocess
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time
import threading
import tempfile
import shutil
import glob

# ========================== AUTO UAC ELEVATION ==========================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, f'"{script}" {params}', None, 1
    )
    return ret > 32

if not is_admin():
    if run_as_admin():
        sys.exit(0)
    else:
        ctypes.windll.user32.MessageBoxW(
            0,
            "This program requires Administrator privileges!\nPlease accept the UAC prompt.",
            "Permission Error", 0x10
        )
        sys.exit(1)

# ========================== LICENSE AGREEMENT ==========================

def show_license_agreement():
    agreed = [False]

    dlg = tk.Tk()
    dlg.title("License Agreement — Arasswys Runner")
    dlg.configure(bg="#1a1a2e")
    dlg.resizable(True, True)
    dlg.minsize(600, 550)

    # Set initial size
    win_w, win_h = 720, 650
    scr_w = dlg.winfo_screenwidth()
    scr_h = dlg.winfo_screenheight()
    x = (scr_w - win_w) // 2
    y = (scr_h - win_h) // 2
    dlg.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # Make rows/cols expandable
    dlg.columnconfigure(0, weight=1)
    dlg.rowconfigure(2, weight=1)  # text area row expands

    # Row 0: Icon + Title
    header_frame = tk.Frame(dlg, bg="#1a1a2e")
    header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))
    header_frame.columnconfigure(0, weight=1)

    tk.Label(header_frame, text="⚠️", font=("Segoe UI", 42),
             fg="#ffd700", bg="#1a1a2e").grid(row=0, column=0)
    tk.Label(header_frame, text="END USER LICENSE AGREEMENT",
             font=("Segoe UI", 16, "bold"), fg="#e94560", bg="#1a1a2e").grid(row=1, column=0)
    tk.Label(header_frame, text="Arasswys Runner — Privilege Escalation Tool",
             font=("Segoe UI", 11), fg="#a0a0a0", bg="#1a1a2e").grid(row=2, column=0, pady=(2, 0))

    # Row 1: Small separator
    tk.Frame(dlg, bg="#e94560", height=2).grid(row=1, column=0, sticky="ew", padx=30, pady=8)

    # Row 2: License text (expandable)
    text_frame = tk.Frame(dlg, bg="#0f3460", padx=3, pady=3)
    text_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 10))
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)

    license_text = tk.Text(text_frame, font=("Segoe UI", 10), bg="#0a0a1a", fg="#cccccc",
                           wrap=tk.WORD, relief=tk.FLAT, bd=10, highlightthickness=0,
                           spacing1=2, spacing3=2)
    license_text.grid(row=0, column=0, sticky="nsew")

    text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=license_text.yview)
    text_scroll.grid(row=0, column=1, sticky="ns")
    license_text.config(yscrollcommand=text_scroll.set)

    agreement = """DISCLAIMER AND TERMS OF USE

By using this software ("Arasswys Runner"), you acknowledge and agree to the following terms:

1. ASSUMPTION OF RISK
This software provides advanced system privilege escalation capabilities including but not limited to: SYSTEM, TrustedInstaller, WinRE, Network Service, and Local Service level access. These operations modify system-level security contexts and can potentially cause irreversible damage to your operating system.

2. NO WARRANTY
This software is provided "AS IS" without warranty of any kind, either express or implied, including but not limited to the implied warranties of merchantability, fitness for a particular purpose, or non-infringement.

3. LIMITATION OF LIABILITY
In no event shall the authors, developers, or contributors be held liable for any direct, indirect, incidental, special, exemplary, or consequential damages (including but not limited to data loss, system corruption, security breaches, or hardware damage) arising from the use or inability to use this software.

4. USER RESPONSIBILITY
YOU are solely responsible for any actions performed using this software. The developers accept NO responsibility for:
  - Damage to your operating system or files
  - Security vulnerabilities introduced by privilege escalation
  - Loss of data or system instability
  - Any legal consequences arising from misuse
  - Unauthorized access to systems you do not own

5. INTENDED USE
This tool is intended for educational purposes, system administration, and authorized security research ONLY. Using this software on systems you do not own or without proper authorization may violate local, state, or federal laws.

6. WINRE MODE WARNING
The WinRE mode creates a virtual RAM disk and mounts Windows Recovery Environment files. This process modifies disk configurations and should be used with extreme caution.

7. ACCEPTANCE
By clicking "I Accept", you confirm that you have read, understood, and agree to be bound by these terms. If you do not agree, click "I Decline" to exit.

USE AT YOUR OWN RISK.

Credits: youtube.com/@Slotshz"""

    license_text.insert("1.0", agreement)
    license_text.config(state=tk.DISABLED)

    # Row 3: Checkbox + Buttons (fixed at bottom)
    bottom_frame = tk.Frame(dlg, bg="#1a1a2e")
    bottom_frame.grid(row=3, column=0, sticky="ew", padx=30, pady=(5, 20))
    bottom_frame.columnconfigure(0, weight=1)

    # Checkbox
    agree_var = tk.BooleanVar(value=False)

    def on_check_changed(*args):
        if agree_var.get():
            accept_btn.config(state=tk.NORMAL, bg="#00cc66")
        else:
            accept_btn.config(state=tk.DISABLED, bg="#555555")

    agree_var.trace_add("write", on_check_changed)

    chk = tk.Checkbutton(bottom_frame,
                         text="  I have read and understood the above terms",
                         variable=agree_var,
                         font=("Segoe UI", 10, "bold"), fg="#ffd700", bg="#1a1a2e",
                         selectcolor="#0f3460", activebackground="#1a1a2e",
                         cursor="hand2")
    chk.grid(row=0, column=0, pady=(0, 12), sticky="w")

    # Buttons frame
    btn_frame = tk.Frame(bottom_frame, bg="#1a1a2e")
    btn_frame.grid(row=1, column=0)

    def on_accept():
        if agree_var.get():
            agreed[0] = True
            dlg.destroy()

    def on_decline():
        agreed[0] = False
        dlg.destroy()

    accept_btn = tk.Button(btn_frame, text="✅  I Accept — Continue",
                           font=("Segoe UI", 13, "bold"),
                           bg="#555555", fg="white", activebackground="#00aa55",
                           disabledforeground="#888888",
                           relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                           state=tk.DISABLED,
                           command=on_accept)
    accept_btn.pack(side=tk.LEFT, padx=15)

    decline_btn = tk.Button(btn_frame, text="❌  I Decline — Exit",
                            font=("Segoe UI", 13, "bold"),
                            bg="#e94560", fg="white", activebackground="#c73e54",
                            relief=tk.FLAT, padx=30, pady=10, cursor="hand2",
                            command=on_decline)
    decline_btn.pack(side=tk.LEFT, padx=15)

    dlg.protocol("WM_DELETE_WINDOW", on_decline)

    # Focus
    dlg.focus_force()
    dlg.lift()

    dlg.mainloop()
    return agreed[0]


# ========================== LOADING SCREEN ==========================

class LoadingScreen:
    def __init__(self, parent):
        self.parent = parent
        self.overlay = None
        self.progress_var = None
        self.status_var = None
        self.detail_var = None
        self.dots_count = 0
        self.animating = False

    def show(self, title="Preparing WinRE Environment..."):
        self.overlay = tk.Toplevel(self.parent)
        self.overlay.title("WinRE Loading")
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="#0a0a1a")
        self.overlay.overrideredirect(True)
        self.overlay.resizable(False, False)

        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()
        w, h = 520, 340
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.overlay.geometry(f"{w}x{h}+{x}+{y}")

        border = tk.Frame(self.overlay, bg="#ffffff", padx=2, pady=2)
        border.pack(fill=tk.BOTH, expand=True)
        inner = tk.Frame(border, bg="#0a0a1a")
        inner.pack(fill=tk.BOTH, expand=True)

        tk.Label(inner, text="💿", font=("Segoe UI", 40), fg="#ffffff", bg="#0a0a1a").pack(pady=(25, 5))
        tk.Label(inner, text=title, font=("Segoe UI", 14, "bold"), fg="#ffffff", bg="#0a0a1a").pack(pady=(0, 5))

        self.status_var = tk.StringVar(value="Initializing...")
        tk.Label(inner, textvariable=self.status_var, font=("Segoe UI", 11),
                 fg="#00d2ff", bg="#0a0a1a").pack(pady=(5, 10))

        style = ttk.Style()
        style.theme_use('default')
        style.configure("WinRE.Horizontal.TProgressbar",
                        troughcolor='#1a1a2e', background='#00cc66',
                        darkcolor='#00cc66', lightcolor='#00ff88', bordercolor='#1a1a2e')
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(inner, variable=self.progress_var, maximum=100,
                                            style="WinRE.Horizontal.TProgressbar", length=420)
        self.progress_bar.pack(pady=(0, 10))

        self.detail_var = tk.StringVar(value="")
        tk.Label(inner, textvariable=self.detail_var, font=("Consolas", 9),
                 fg="#808080", bg="#0a0a1a", wraplength=470).pack(pady=(0, 5))
        tk.Label(inner, text="⚠ Please do not close the application during this process",
                 font=("Segoe UI", 9, "italic"), fg="#ffd700", bg="#0a0a1a").pack(pady=(5, 15))

        self.overlay.update()
        self.animating = True
        self._animate_dots()

    def _animate_dots(self):
        if not self.animating or not self.overlay:
            return
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        try:
            current = self.status_var.get()
            base = current.rstrip(".")
            self.status_var.set(f"{base}{dots}")
            self.overlay.after(500, self._animate_dots)
        except:
            pass

    def update_status(self, status, progress=None, detail=None):
        try:
            if self.status_var:
                self.status_var.set(status)
            if progress is not None and self.progress_var:
                self.progress_var.set(progress)
            if detail is not None and self.detail_var:
                self.detail_var.set(detail)
            if self.overlay:
                self.overlay.update()
        except:
            pass

    def close(self):
        self.animating = False
        if self.overlay:
            try:
                self.overlay.destroy()
            except:
                pass
            self.overlay = None


# ========================== Windows API Constants ==========================

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
TOKEN_ALL_ACCESS = 0x000F01FF
TOKEN_DUPLICATE = 0x0002
TOKEN_QUERY = 0x0008
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_IMPERSONATE = 0x0004
TOKEN_ASSIGN_PRIMARY = 0x0001
TOKEN_ADJUST_DEFAULT = 0x0080
TOKEN_ADJUST_SESSIONID = 0x0100
SE_PRIVILEGE_ENABLED = 0x00000002
SE_PRIVILEGE_ENABLED_BY_DEFAULT = 0x00000001
SecurityImpersonation = 2
SecurityDelegation = 3
TokenPrimary = 1
TokenImpersonation = 2
CREATE_NEW_CONSOLE = 0x00000010
CREATE_UNICODE_ENVIRONMENT = 0x00000400
NORMAL_PRIORITY_CLASS = 0x00000020
LOGON_WITH_PROFILE = 0x00000001
SC_MANAGER_CONNECT = 0x0001
SC_MANAGER_ALL_ACCESS = 0xF003F
SERVICE_START = 0x0010
SERVICE_STOP = 0x0020
SERVICE_QUERY_STATUS = 0x0004
SERVICE_ALL_ACCESS = 0xF01FF
SERVICE_RUNNING = 0x00000004
MAXIMUM_ALLOWED = 0x02000000
TH32CS_SNAPPROCESS = 0x00000002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
DACL_SECURITY_INFORMATION = 0x00000004
ACL_REVISION = 2
GENERIC_ALL = 0x10000000
READ_CONTROL = 0x00020000
WRITE_DAC = 0x00040000
WINSTA_ALL_ACCESS = 0x37F
DESKTOP_ALL_ACCESS = 0x01FF

# ========================== Structures ==========================

class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD), ("Privileges", LUID_AND_ATTRIBUTES * 1)]

class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD), ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR), ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(wintypes.BYTE)),
        ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD),
    ]

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260),
    ]

class SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", wintypes.DWORD), ("dwCurrentState", wintypes.DWORD),
        ("dwControlsAccepted", wintypes.DWORD), ("dwWin32ExitCode", wintypes.DWORD),
        ("dwServiceSpecificExitCode", wintypes.DWORD),
        ("dwCheckPoint", wintypes.DWORD), ("dwWaitHint", wintypes.DWORD),
    ]

# ========================== DLL Loading ==========================

advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
shell32 = ctypes.WinDLL("shell32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
try:
    userenv = ctypes.WinDLL("userenv", use_last_error=True)
except:
    userenv = None

# ========================== FUNCTION PROTOTYPES ==========================

kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.GetCurrentProcess.restype = wintypes.HANDLE
kernel32.GetCurrentProcess.argtypes = []
kernel32.GetCurrentProcessId.restype = wintypes.DWORD
kernel32.GetCurrentProcessId.argtypes = []
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.Process32FirstW.restype = wintypes.BOOL
kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32NextW.restype = wintypes.BOOL
kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.ProcessIdToSessionId.restype = wintypes.BOOL
kernel32.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
kernel32.LocalFree.restype = wintypes.HANDLE
kernel32.LocalFree.argtypes = [wintypes.HANDLE]
advapi32.OpenProcessToken.restype = wintypes.BOOL
advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL
advapi32.LookupPrivilegeValueW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(LUID)]
advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL
advapi32.AdjustTokenPrivileges.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TOKEN_PRIVILEGES), wintypes.DWORD, ctypes.POINTER(TOKEN_PRIVILEGES), ctypes.POINTER(wintypes.DWORD)]
advapi32.DuplicateTokenEx.restype = wintypes.BOOL
advapi32.DuplicateTokenEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
advapi32.SetTokenInformation.restype = wintypes.BOOL
advapi32.SetTokenInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD]
advapi32.GetTokenInformation.restype = wintypes.BOOL
advapi32.GetTokenInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
advapi32.ImpersonateLoggedOnUser.restype = wintypes.BOOL
advapi32.ImpersonateLoggedOnUser.argtypes = [wintypes.HANDLE]
advapi32.SetThreadToken.restype = wintypes.BOOL
advapi32.SetThreadToken.argtypes = [ctypes.c_void_p, wintypes.HANDLE]
advapi32.RevertToSelf.restype = wintypes.BOOL
advapi32.RevertToSelf.argtypes = []
advapi32.CreateProcessAsUserW.restype = wintypes.BOOL
advapi32.CreateProcessAsUserW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p, wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)]
advapi32.CreateProcessWithTokenW.restype = wintypes.BOOL
advapi32.CreateProcessWithTokenW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)]
advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
advapi32.ConvertStringSidToSidW.restype = wintypes.BOOL
advapi32.ConvertStringSidToSidW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p)]
advapi32.GetLengthSid.restype = wintypes.DWORD
advapi32.GetLengthSid.argtypes = [ctypes.c_void_p]
advapi32.InitializeAcl.restype = wintypes.BOOL
advapi32.InitializeAcl.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]
advapi32.AddAccessAllowedAce.restype = wintypes.BOOL
advapi32.AddAccessAllowedAce.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
advapi32.InitializeSecurityDescriptor.restype = wintypes.BOOL
advapi32.InitializeSecurityDescriptor.argtypes = [ctypes.c_void_p, wintypes.DWORD]
advapi32.SetSecurityDescriptorDacl.restype = wintypes.BOOL
advapi32.SetSecurityDescriptorDacl.argtypes = [ctypes.c_void_p, wintypes.BOOL, ctypes.c_void_p, wintypes.BOOL]
SC_HANDLE = ctypes.c_void_p
advapi32.OpenSCManagerW.restype = SC_HANDLE
advapi32.OpenSCManagerW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
advapi32.OpenServiceW.restype = SC_HANDLE
advapi32.OpenServiceW.argtypes = [SC_HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
advapi32.StartServiceW.restype = wintypes.BOOL
advapi32.StartServiceW.argtypes = [SC_HANDLE, wintypes.DWORD, ctypes.c_void_p]
advapi32.QueryServiceStatus.restype = wintypes.BOOL
advapi32.QueryServiceStatus.argtypes = [SC_HANDLE, ctypes.POINTER(SERVICE_STATUS)]
advapi32.CloseServiceHandle.restype = wintypes.BOOL
advapi32.CloseServiceHandle.argtypes = [SC_HANDLE]
user32.GetProcessWindowStation.restype = wintypes.HANDLE
user32.GetProcessWindowStation.argtypes = []
user32.OpenWindowStationW.restype = wintypes.HANDLE
user32.OpenWindowStationW.argtypes = [wintypes.LPCWSTR, wintypes.BOOL, wintypes.DWORD]
user32.OpenDesktopW.restype = wintypes.HANDLE
user32.OpenDesktopW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
user32.CloseWindowStation.restype = wintypes.BOOL
user32.CloseWindowStation.argtypes = [wintypes.HANDLE]
user32.CloseDesktop.restype = wintypes.BOOL
user32.CloseDesktop.argtypes = [wintypes.HANDLE]
user32.SetUserObjectSecurity.restype = wintypes.BOOL
user32.SetUserObjectSecurity.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
user32.GetUserObjectSecurity.restype = wintypes.BOOL
user32.GetUserObjectSecurity.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
shell32.ShellExecuteW.restype = wintypes.HINSTANCE
shell32.ShellExecuteW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_int]
if userenv:
    userenv.CreateEnvironmentBlock.restype = wintypes.BOOL
    userenv.CreateEnvironmentBlock.argtypes = [ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.BOOL]
    userenv.DestroyEnvironmentBlock.restype = wintypes.BOOL
    userenv.DestroyEnvironmentBlock.argtypes = [ctypes.c_void_p]

# ========================== All Privilege Names ==========================

ALL_PRIVILEGES = [
    "SeAssignPrimaryTokenPrivilege","SeAuditPrivilege","SeBackupPrivilege",
    "SeChangeNotifyPrivilege","SeCreateGlobalPrivilege","SeCreatePagefilePrivilege",
    "SeCreatePermanentPrivilege","SeCreateSymbolicLinkPrivilege",
    "SeCreateTokenPrivilege","SeDebugPrivilege",
    "SeDelegateSessionUserImpersonatePrivilege","SeEnableDelegationPrivilege",
    "SeImpersonatePrivilege","SeIncreaseBasePriorityPrivilege",
    "SeIncreaseQuotaPrivilege","SeIncreaseWorkingSetPrivilege",
    "SeLoadDriverPrivilege","SeLockMemoryPrivilege","SeMachineAccountPrivilege",
    "SeManageVolumePrivilege","SeProfileSingleProcessPrivilege",
    "SeRelabelPrivilege","SeRemoteShutdownPrivilege","SeRestorePrivilege",
    "SeSecurityPrivilege","SeShutdownPrivilege","SeSyncAgentPrivilege",
    "SeSystemEnvironmentPrivilege","SeSystemProfilePrivilege",
    "SeSystemtimePrivilege","SeTakeOwnershipPrivilege","SeTcbPrivilege",
    "SeTimeZonePrivilege","SeTrustedCredManAccessPrivilege",
    "SeUndockPrivilege","SeUnsolicitedInputPrivilege",
]
NETWORK_SERVICE_PROCESSES = ["nlasvc","dnscache","LanmanWorkstation","CryptSvc","TermService","Dhcp","NlaSvc","WinHttpAutoProxySvc"]
LOCAL_SERVICE_PROCESSES = ["EventLog","nsi","W32Time","WinHttpAutoProxySvc","AudioSrv","fdPHost","FontCache","TimeBrokerSvc","SCardSvr"]
SID_NETWORK_SERVICE = "S-1-5-20"
SID_LOCAL_SERVICE = "S-1-5-19"
SID_LOCAL_SYSTEM = "S-1-5-18"
SID_EVERYONE = "S-1-1-0"
WINRE_DRIVE = "X:"
WINRE_SYSTEM32 = "X:\\Windows\\System32"

# ========================== WinRE RAM DISK ENGINE ==========================

class WinREDiskManager:
    def __init__(self, log_callback=None, loading_screen=None):
        self.log = log_callback or (lambda m: None)
        self.loading = loading_screen
        self.vhd_path = None
        self.mounted = False

    def _upd(self, s, p=None, d=None):
        if self.loading: self.loading.update_status(s, p, d)

    def is_x_drive_ready(self):
        return os.path.isdir(WINRE_SYSTEM32)

    def find_winre_wim(self):
        self.log("   🔍 Searching for WinRE.wim...")
        self._upd("Searching for WinRE.wim...", 5, "Checking standard locations")
        paths = []
        try:
            r = subprocess.run(["reagentc","/info"], capture_output=True, text=True, timeout=15)
            for line in r.stdout.splitlines():
                if "winre.wim" in line.lower():
                    parts = line.split("\\")
                    for i,p in enumerate(parts):
                        if p.lower()=="winre.wim":
                            path = "\\".join(parts[:i+1]).strip()
                            idx = path.find("\\\\?\\")
                            if idx>=0: path=path[idx:]
                            paths.append(path); break
        except: pass
        sd = os.environ.get("SystemDrive","C:")
        paths += [f"{sd}\\Recovery\\WindowsRE\\Winre.wim",f"{sd}\\Windows\\System32\\Recovery\\Winre.wim",f"{sd}\\Recovery\\Winre.wim"]
        for L in "CDEFGHIJKLMNOPQRSTUVWYZ":
            paths += [f"{L}:\\Recovery\\WindowsRE\\Winre.wim",f"{L}:\\Windows\\System32\\Recovery\\Winre.wim",f"{L}:\\Recovery\\Winre.wim",f"{L}:\\Sources\\Winre.wim"]
        ck=set()
        for p in paths:
            pl=p.lower()
            if pl in ck: continue
            ck.add(pl)
            if os.path.isfile(p):
                sz=os.path.getsize(p)/(1024*1024)
                self.log(f"   ✅ Found: {p} ({sz:.1f} MB)")
                self._upd("WinRE.wim found!",15,p); return p
        self.log("   ⚠ Not found, checking Recovery partition...")
        self._upd("Checking Recovery partition...",10)
        return self._try_mount_recovery()

    def _try_mount_recovery(self):
        try:
            sf=tempfile.NamedTemporaryFile(mode='w',suffix='.txt',delete=False); sf.write("list volume\n"); sf.close()
            r=subprocess.run(["diskpart","/s",sf.name],capture_output=True,text=True,timeout=30); os.unlink(sf.name)
            rv=None
            for line in r.stdout.splitlines():
                lo=line.lower()
                if "recovery" in lo or "kurtarma" in lo:
                    pts=line.split()
                    for i,p in enumerate(pts):
                        if p.lower()=="volume" and i+1<len(pts):
                            try: rv=int(pts[i+1])
                            except: pass
                            break
                    if rv is not None: break
            if rv is None: return None
            used={L for L in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{L}:")}
            al=None
            for L in "ZYXWVUTSRQPONMLKJIHGFED":
                if L not in used and L!='X': al=L; break
            if not al: return None
            sf2=tempfile.NamedTemporaryFile(mode='w',suffix='.txt',delete=False)
            sf2.write(f"select volume {rv}\nassign letter={al}\n"); sf2.close()
            subprocess.run(["diskpart","/s",sf2.name],capture_output=True,text=True,timeout=30); os.unlink(sf2.name)
            time.sleep(1)
            for sub in ["Recovery\\WindowsRE\\Winre.wim","Winre.wim","Recovery\\Winre.wim"]:
                cp=f"{al}:\\{sub}"
                if os.path.isfile(cp):
                    sz=os.path.getsize(cp)/(1024*1024)
                    self.log(f"   ✅ Found: {cp} ({sz:.1f} MB)"); return cp
            sf3=tempfile.NamedTemporaryFile(mode='w',suffix='.txt',delete=False)
            sf3.write(f"select volume {rv}\nremove letter={al}\n"); sf3.close()
            subprocess.run(["diskpart","/s",sf3.name],capture_output=True,text=True,timeout=30); os.unlink(sf3.name)
            return None
        except: return None

    def create_ram_disk_and_apply_wim(self, wim_path):
        self.log("   📀 Creating RAM disk...")
        self._upd("Creating virtual disk...",20,"Preparing VHDX")
        if os.path.exists("X:") and self.is_x_drive_ready():
            self.log("   ✅ X: already ready"); self._upd("X: ready!",100); self.mounted=True; return True
        wsz=os.path.getsize(wim_path)/(1024*1024)
        vsz=max(int(wsz*3),1024)
        self.vhd_path=os.path.join(tempfile.gettempdir(),"winre_ramdisk.vhdx")
        if os.path.exists(self.vhd_path): self._detach(); 
        try: os.remove(self.vhd_path)
        except: pass
        self._upd("Creating VHDX...",30,f"Size: {vsz} MB")
        ok=self._create_vhd_dp(vsz)
        if not ok: self._upd("Trying PowerShell...",35); ok=self._create_vhd_ps(vsz)
        if not ok: self.log("   ❌ VHD failed"); return False
        self._upd("Applying WinRE.wim...",50,"This may take 1-3 minutes")
        self.log("   📦 Applying WIM...")
        ok=self._apply_dism(wim_path)
        if not ok: self._upd("Alt extraction...",70); ok=self._apply_7z(wim_path)
        if ok:
            self.mounted=True; self._upd("WinRE X: ready!",100,WINRE_SYSTEM32)
            self.log("   ✅ WinRE on X:!"); return True
        self.log("   ❌ Apply failed"); self._cleanup(); return False

    def _create_vhd_dp(self,sz):
        try:
            s=f'create vdisk file="{self.vhd_path}" maximum={sz} type=expandable\nselect vdisk file="{self.vhd_path}"\nattach vdisk\ncreate partition primary\nformat fs=ntfs quick label="WinRE"\nassign letter=X\n'
            sf=tempfile.NamedTemporaryFile(mode='w',suffix='.txt',delete=False); sf.write(s); sf.close()
            subprocess.run(["diskpart","/s",sf.name],capture_output=True,text=True,timeout=120); os.unlink(sf.name)
            return os.path.exists("X:")
        except: return False

    def _create_vhd_ps(self,sz):
        try:
            sb=sz*1024*1024
            ps=f"$v='{self.vhd_path}';if(Test-Path $v){{Remove-Item $v -Force}};New-VHD -Path $v -SizeBytes {sb} -Dynamic|Out-Null;Mount-VHD -Path $v|Out-Null;$d=Get-VHD -Path $v|Get-Disk;Initialize-Disk -Number $d.Number -PartitionStyle MBR -Confirm:$false|Out-Null;New-Partition -DiskNumber $d.Number -UseMaximumSize -DriveLetter X|Out-Null;Format-Volume -DriveLetter X -FileSystem NTFS -NewFileSystemLabel 'WinRE' -Confirm:$false|Out-Null"
            subprocess.run(["powershell","-ExecutionPolicy","Bypass","-Command",ps],capture_output=True,text=True,timeout=120)
            return os.path.exists("X:")
        except: return False

    def _apply_dism(self,wim):
        try:
            d=os.path.join(os.environ.get("SystemRoot","C:\\Windows"),"System32","dism.exe")
            r=subprocess.run([d,"/Apply-Image",f"/ImageFile:{wim}","/Index:1","/ApplyDir:X:\\"],capture_output=True,text=True,timeout=600)
            return r.returncode==0
        except: return False

    def _apply_7z(self,wim):
        try:
            for p in ["C:\\Program Files\\7-Zip\\7z.exe","C:\\Program Files (x86)\\7-Zip\\7z.exe"]:
                if os.path.isfile(p):
                    r=subprocess.run([p,"x",wim,"-oX:\\","-y"],capture_output=True,text=True,timeout=600)
                    if r.returncode==0 and os.path.isdir("X:\\Windows"): return True
            return False
        except: return False

    def _detach(self):
        if not self.vhd_path: return
        try:
            sf=tempfile.NamedTemporaryFile(mode='w',suffix='.txt',delete=False)
            sf.write(f'select vdisk file="{self.vhd_path}"\ndetach vdisk\n'); sf.close()
            subprocess.run(["diskpart","/s",sf.name],capture_output=True,text=True,timeout=30); os.unlink(sf.name)
        except: pass

    def _cleanup(self):
        self._detach()
        if self.vhd_path and os.path.exists(self.vhd_path):
            try: os.remove(self.vhd_path)
            except: pass

    def unmount(self):
        if self.mounted: self._detach(); self.mounted=False

_winre_manager = None

def ensure_winre_x_drive(log_cb=None, ls=None):
    global _winre_manager
    log = log_cb or (lambda m: None)
    if os.path.isdir(WINRE_SYSTEM32): log("✅ X:\\Windows\\System32 ready"); return True
    log("📀 Preparing X:...")
    _winre_manager = WinREDiskManager(log, ls)
    wim = _winre_manager.find_winre_wim()
    if not wim: log("❌ WinRE.wim not found!"); return False
    return _winre_manager.create_ram_disk_and_apply_wim(wim)

def cleanup_winre_x_drive(log_cb=None):
    global _winre_manager
    if _winre_manager: _winre_manager.unmount(); _winre_manager=None

# ========================== FILE TYPE RESOLVER ==========================

def resolve_app_and_args(app_path, is_winre_mode=False):
    ext = os.path.splitext(app_path)[1].lower()
    s32 = os.path.join(os.environ.get("SystemRoot","C:\\Windows"),"System32")
    if ext == ".exe":
        if is_winre_mode:
            bn = os.path.basename(app_path).lower()
            if bn == "cmd.exe":
                return app_path, f'"{app_path}" /k "title WinRE - {WINRE_SYSTEM32} && cd /d {WINRE_SYSTEM32}"'
            elif bn == "powershell.exe":
                return app_path, f'"{app_path}" -NoExit -Command "$Host.UI.RawUI.WindowTitle = \'WinRE - {WINRE_SYSTEM32}\'; Set-Location \'{WINRE_SYSTEM32}\'"'
        return app_path, None
    elif ext == ".msc": m=os.path.join(s32,"mmc.exe"); return m, f'"{m}" "{app_path}"'
    elif ext in (".bat",".cmd"): c=os.path.join(s32,"cmd.exe"); return c, f'"{c}" /c "{app_path}"'
    elif ext == ".ps1":
        p=os.path.join(s32,"WindowsPowerShell","v1.0","powershell.exe")
        if not os.path.exists(p): p="powershell.exe"
        return p, f'"{p}" -ExecutionPolicy Bypass -NoExit -File "{app_path}"'
    elif ext in (".vbs",".vbe"): c=os.path.join(s32,"cscript.exe"); return c, f'"{c}" //nologo "{app_path}"'
    elif ext in (".js",".jse",".wsf"): c=os.path.join(s32,"cscript.exe"); return c, f'"{c}" //nologo "{app_path}"'
    elif ext == ".py": p=sys.executable or "python.exe"; return p, f'"{p}" "{app_path}"'
    elif ext == ".cpl": c=os.path.join(s32,"control.exe"); return c, f'"{c}" "{app_path}"'
    elif ext == ".reg": r=os.path.join(os.environ.get("SystemRoot","C:\\Windows"),"regedit.exe"); return r, f'"{r}" "{app_path}"'
    elif ext in (".msi",".msp"): m=os.path.join(s32,"msiexec.exe"); return m, f'"{m}" /i "{app_path}"'
    else: c=os.path.join(s32,"cmd.exe"); return c, f'"{c}" /c start "" "{app_path}"'

def get_file_type_description(app_path):
    ext = os.path.splitext(app_path)[1].lower()
    d={".exe":"Direct executable",".msc":"MMC → mmc.exe",".bat":"Batch → cmd.exe",".cmd":"Command → cmd.exe",
       ".ps1":"PowerShell → powershell.exe",".vbs":"VBScript → cscript.exe",".vbe":"VBScript → cscript.exe",
       ".js":"JScript → cscript.exe",".jse":"JScript → cscript.exe",".wsf":"WSF → cscript.exe",
       ".py":"Python → python.exe",".cpl":"Control Panel → control.exe",".reg":"Registry → regedit.exe",
       ".msi":"Installer → msiexec.exe",".msp":"Patch → msiexec.exe"}
    return d.get(ext, f"Unknown ({ext}) → cmd.exe")

# ========================== Helper Functions ==========================

def enable_privilege(pn):
    hT=wintypes.HANDLE()
    if not advapi32.OpenProcessToken(kernel32.GetCurrentProcess(),TOKEN_ALL_ACCESS,ctypes.byref(hT)): return False
    luid=LUID()
    if not advapi32.LookupPrivilegeValueW(None,pn,ctypes.byref(luid)): kernel32.CloseHandle(hT); return False
    tp=TOKEN_PRIVILEGES(); tp.PrivilegeCount=1; tp.Privileges[0].Luid=luid; tp.Privileges[0].Attributes=SE_PRIVILEGE_ENABLED
    r=advapi32.AdjustTokenPrivileges(hT,False,ctypes.byref(tp),ctypes.sizeof(tp),None,None); e=ctypes.get_last_error()
    kernel32.CloseHandle(hT); return r and e==0

def enable_current_process_privileges():
    for p in ["SeDebugPrivilege","SeImpersonatePrivilege","SeAssignPrimaryTokenPrivilege","SeIncreaseQuotaPrivilege","SeTcbPrivilege","SeBackupPrivilege","SeRestorePrivilege"]:
        enable_privilege(p)

def get_pid_by_name(n):
    sn=kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0)
    if sn==wintypes.HANDLE(INVALID_HANDLE_VALUE).value or sn is None: return None
    pe=PROCESSENTRY32W(); pe.dwSize=ctypes.sizeof(PROCESSENTRY32W); pids=[]
    if kernel32.Process32FirstW(sn,ctypes.byref(pe)):
        while True:
            if pe.szExeFile.lower()==n.lower(): pids.append(pe.th32ProcessID)
            if not kernel32.Process32NextW(sn,ctypes.byref(pe)): break
    kernel32.CloseHandle(sn); return pids[0] if pids else None

def get_all_pids_by_name(n):
    sn=kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0)
    if sn==wintypes.HANDLE(INVALID_HANDLE_VALUE).value or sn is None: return []
    pe=PROCESSENTRY32W(); pe.dwSize=ctypes.sizeof(PROCESSENTRY32W); pids=[]
    if kernel32.Process32FirstW(sn,ctypes.byref(pe)):
        while True:
            if pe.szExeFile.lower()==n.lower(): pids.append(pe.th32ProcessID)
            if not kernel32.Process32NextW(sn,ctypes.byref(pe)): break
    kernel32.CloseHandle(sn); return pids

def open_process_token_ex(pid, desired=TOKEN_ALL_ACCESS):
    for acc in [PROCESS_QUERY_INFORMATION,PROCESS_QUERY_LIMITED_INFORMATION,MAXIMUM_ALLOWED]:
        hP=kernel32.OpenProcess(acc,False,pid)
        if hP and hP!=wintypes.HANDLE(0).value:
            hT=wintypes.HANDLE()
            for ta in [desired,TOKEN_ALL_ACCESS,TOKEN_DUPLICATE|TOKEN_QUERY|TOKEN_IMPERSONATE,TOKEN_DUPLICATE|TOKEN_QUERY,MAXIMUM_ALLOWED]:
                if advapi32.OpenProcessToken(hP,ta,ctypes.byref(hT)): kernel32.CloseHandle(hP); return hT
            kernel32.CloseHandle(hP)
    return None

def get_token_user_sid_string(hT):
    bs=wintypes.DWORD(0); advapi32.GetTokenInformation(hT,1,None,0,ctypes.byref(bs))
    if bs.value==0: return None
    buf=ctypes.create_string_buffer(bs.value)
    if not advapi32.GetTokenInformation(hT,1,buf,bs.value,ctypes.byref(bs)): return None
    sp=ctypes.cast(buf,ctypes.POINTER(ctypes.c_void_p))[0]; ss=wintypes.LPWSTR()
    if advapi32.ConvertSidToStringSidW(sp,ctypes.byref(ss)):
        r=ss.value; kernel32.LocalFree(ctypes.cast(ss,wintypes.HANDLE)); return r
    return None

def get_system_token():
    enable_current_process_privileges()
    for pn in ["winlogon.exe","lsass.exe","services.exe","svchost.exe"]:
        pid=get_pid_by_name(pn)
        if pid:
            hT=open_process_token_ex(pid)
            if hT: return hT
    return None

def find_service_process_token(tsid, svcs, log_cb=None):
    log=log_cb or (lambda m: None); enable_current_process_privileges()
    for sn in svcs:
        try:
            r=subprocess.run(["sc","query",sn],capture_output=True,text=True,timeout=5)
            if "RUNNING" not in r.stdout: subprocess.run(["sc","start",sn],capture_output=True,text=True,timeout=10); time.sleep(0.3)
        except: pass
    pids=get_all_pids_by_name("svchost.exe")
    for pid in pids:
        hT=open_process_token_ex(pid)
        if not hT: continue
        sid=get_token_user_sid_string(hT)
        if sid and sid==tsid: return hT
        kernel32.CloseHandle(hT)
    sn=kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0)
    if sn==wintypes.HANDLE(INVALID_HANDLE_VALUE).value or sn is None: return None
    pe=PROCESSENTRY32W(); pe.dwSize=ctypes.sizeof(PROCESSENTRY32W); ck=set(pids)
    if kernel32.Process32FirstW(sn,ctypes.byref(pe)):
        while True:
            pid=pe.th32ProcessID
            if pid not in ck and pid>4:
                hT=open_process_token_ex(pid)
                if hT:
                    sid=get_token_user_sid_string(hT)
                    if sid and sid==tsid: kernel32.CloseHandle(sn); return hT
                    kernel32.CloseHandle(hT)
            if not kernel32.Process32NextW(sn,ctypes.byref(pe)): break
    kernel32.CloseHandle(sn); return None

def duplicate_token(hT, imp=SecurityDelegation, tt=TokenPrimary):
    hN=wintypes.HANDLE()
    if advapi32.DuplicateTokenEx(hT,MAXIMUM_ALLOWED,None,imp,tt,ctypes.byref(hN)): return hN
    if advapi32.DuplicateTokenEx(hT,MAXIMUM_ALLOWED,None,SecurityImpersonation,tt,ctypes.byref(hN)): return hN
    return None

def enable_all_privileges_on_token(hT):
    c=0
    for pn in ALL_PRIVILEGES:
        luid=LUID()
        if advapi32.LookupPrivilegeValueW(None,pn,ctypes.byref(luid)):
            tp=TOKEN_PRIVILEGES(); tp.PrivilegeCount=1; tp.Privileges[0].Luid=luid
            tp.Privileges[0].Attributes=SE_PRIVILEGE_ENABLED|SE_PRIVILEGE_ENABLED_BY_DEFAULT
            if advapi32.AdjustTokenPrivileges(hT,False,ctypes.byref(tp),ctypes.sizeof(tp),None,None):
                if ctypes.get_last_error()==0: c+=1
    return c

def set_token_session_id(hT, sid):
    s=wintypes.DWORD(sid); return advapi32.SetTokenInformation(hT,12,ctypes.byref(s),ctypes.sizeof(s))

def get_current_session_id():
    s=wintypes.DWORD(); kernel32.ProcessIdToSessionId(kernel32.GetCurrentProcessId(),ctypes.byref(s)); return s.value

def grant_winsta_desktop_access(sid_str, log_cb=None):
    pSid=ctypes.c_void_p()
    if not advapi32.ConvertStringSidToSidW(sid_str,ctypes.byref(pSid)): return False
    sc=0
    hW=user32.OpenWindowStationW("WinSta0",False,READ_CONTROL|WRITE_DAC)
    if hW:
        if _add_ace(hW,pSid,WINSTA_ALL_ACCESS|GENERIC_ALL): sc+=1
        user32.CloseWindowStation(hW)
    hD=user32.OpenDesktopW("Default",0,False,READ_CONTROL|WRITE_DAC|DESKTOP_ALL_ACCESS)
    if hD:
        if _add_ace(hD,pSid,DESKTOP_ALL_ACCESS|GENERIC_ALL): sc+=1
        user32.CloseDesktop(hD)
    kernel32.LocalFree(pSid); return sc>0

def _add_ace(hObj, pSid, mask):
    sl=advapi32.GetLengthSid(pSid); asz=1024+sl*2; acl=ctypes.create_string_buffer(asz)
    if not advapi32.InitializeAcl(acl,asz,ACL_REVISION): return False
    es=ctypes.c_void_p()
    if advapi32.ConvertStringSidToSidW(SID_EVERYONE,ctypes.byref(es)):
        advapi32.AddAccessAllowedAce(acl,ACL_REVISION,mask,es); kernel32.LocalFree(es)
    advapi32.AddAccessAllowedAce(acl,ACL_REVISION,mask,pSid)
    ss=ctypes.c_void_p()
    if advapi32.ConvertStringSidToSidW(SID_LOCAL_SYSTEM,ctypes.byref(ss)):
        advapi32.AddAccessAllowedAce(acl,ACL_REVISION,mask,ss); kernel32.LocalFree(ss)
    sd=ctypes.create_string_buffer(40); advapi32.InitializeSecurityDescriptor(sd,1)
    advapi32.SetSecurityDescriptorDacl(sd,True,acl,False)
    si=wintypes.DWORD(DACL_SECURITY_INFORMATION)
    return bool(user32.SetUserObjectSecurity(hObj,ctypes.byref(si),sd))

def impersonate_system():
    st=get_system_token()
    if not st: return False,None
    hI=duplicate_token(st,SecurityImpersonation,TokenImpersonation); kernel32.CloseHandle(st)
    if not hI: return False,None
    if advapi32.ImpersonateLoggedOnUser(hI): return True,hI
    if advapi32.SetThreadToken(None,hI): return True,hI
    kernel32.CloseHandle(hI); return False,None

def revert_impersonation(hI):
    advapi32.RevertToSelf()
    if hI: kernel32.CloseHandle(hI)

def start_ti_svc(log_cb=None):
    hSC=advapi32.OpenSCManagerW(None,None,SC_MANAGER_ALL_ACCESS)
    if not hSC: hSC=advapi32.OpenSCManagerW(None,None,SC_MANAGER_CONNECT)
    if not hSC: return False,"SCM error"
    hS=advapi32.OpenServiceW(hSC,"TrustedInstaller",SERVICE_ALL_ACCESS)
    if not hS: hS=advapi32.OpenServiceW(hSC,"TrustedInstaller",SERVICE_START|SERVICE_QUERY_STATUS)
    if not hS: advapi32.CloseServiceHandle(hSC); return False,"TI open error"
    st=SERVICE_STATUS(); advapi32.QueryServiceStatus(hS,ctypes.byref(st))
    if st.dwCurrentState==SERVICE_RUNNING: advapi32.CloseServiceHandle(hS); advapi32.CloseServiceHandle(hSC); return True,"Running"
    advapi32.StartServiceW(hS,0,None)
    for _ in range(60):
        advapi32.QueryServiceStatus(hS,ctypes.byref(st))
        if st.dwCurrentState==SERVICE_RUNNING: break
        time.sleep(0.3)
    ok=st.dwCurrentState==SERVICE_RUNNING
    advapi32.CloseServiceHandle(hS); advapi32.CloseServiceHandle(hSC)
    return (True,"Started") if ok else (False,"Timeout")

def start_ti_sc(log_cb=None):
    try:
        r=subprocess.run(["sc","query","TrustedInstaller"],capture_output=True,text=True,timeout=10)
        if "RUNNING" in r.stdout: return True,"Running"
        subprocess.run(["sc","start","TrustedInstaller"],capture_output=True,text=True,timeout=30)
        for _ in range(30):
            c=subprocess.run(["sc","query","TrustedInstaller"],capture_output=True,text=True,timeout=10)
            if "RUNNING" in c.stdout: return True,"Started"
            time.sleep(0.5)
        return False,"Failed"
    except Exception as e: return False,str(e)

# ========================== Process Creation ==========================

def _create_m1(hT,app,privs=False,wd=None):
    iw=wd and "X:" in wd.upper()
    exe,cl=resolve_app_and_args(app,iw)
    hD=duplicate_token(hT,SecurityDelegation,TokenPrimary)
    if not hD: return False,"Dup fail"
    set_token_session_id(hD,get_current_session_id())
    pc=enable_all_privileges_on_token(hD) if privs else 0
    si=STARTUPINFOW(); si.cb=ctypes.sizeof(STARTUPINFOW); si.lpDesktop="WinSta0\\Default"
    pi=PROCESS_INFORMATION(); fl=CREATE_NEW_CONSOLE|CREATE_UNICODE_ENVIRONMENT|NORMAL_PRIORITY_CLASS
    sd=wd if wd and os.path.isdir(wd) else None
    env=ctypes.c_void_p(); he=False
    if userenv:
        try: he=userenv.CreateEnvironmentBlock(ctypes.byref(env),hD,False)
        except: pass
    if cl:
        cb=ctypes.create_unicode_buffer(cl)
        r=advapi32.CreateProcessAsUserW(hD,exe,cb,None,None,False,fl,env if he else None,sd,ctypes.byref(si),ctypes.byref(pi))
    else:
        r=advapi32.CreateProcessAsUserW(hD,exe,None,None,None,False,fl,env if he else None,sd,ctypes.byref(si),ctypes.byref(pi))
    e=ctypes.get_last_error()
    if he and env:
        try: userenv.DestroyEnvironmentBlock(env)
        except: pass
    if r:
        kernel32.CloseHandle(pi.hProcess); kernel32.CloseHandle(pi.hThread); kernel32.CloseHandle(hD)
        m=f"PID: {pi.dwProcessId}"
        if privs: m+=f" | {pc} privs"
        return True,m
    kernel32.CloseHandle(hD); return False,f"Err:{e}"

def _create_m2(hT,app,privs=False,wd=None):
    iw=wd and "X:" in wd.upper()
    exe,cl=resolve_app_and_args(app,iw)
    hD=duplicate_token(hT,SecurityImpersonation,TokenPrimary)
    if not hD: return False,"Dup fail"
    set_token_session_id(hD,get_current_session_id())
    pc=enable_all_privileges_on_token(hD) if privs else 0
    si=STARTUPINFOW(); si.cb=ctypes.sizeof(STARTUPINFOW); si.lpDesktop="WinSta0\\Default"
    pi=PROCESS_INFORMATION(); fl=CREATE_NEW_CONSOLE|CREATE_UNICODE_ENVIRONMENT
    sd=wd if wd and os.path.isdir(wd) else None
    if cl:
        cb=ctypes.create_unicode_buffer(cl)
        r=advapi32.CreateProcessWithTokenW(hD,LOGON_WITH_PROFILE,exe,cb,fl,None,sd,ctypes.byref(si),ctypes.byref(pi))
    else:
        r=advapi32.CreateProcessWithTokenW(hD,LOGON_WITH_PROFILE,exe,None,fl,None,sd,ctypes.byref(si),ctypes.byref(pi))
    e=ctypes.get_last_error()
    if r:
        kernel32.CloseHandle(pi.hProcess); kernel32.CloseHandle(pi.hThread); kernel32.CloseHandle(hD)
        m=f"PID: {pi.dwProcessId}"
        if privs: m+=f" | {pc} privs"
        return True,m
    kernel32.CloseHandle(hD); return False,f"Err:{e}"

def launch_process(hT,app,privs=False,wd=None):
    ok,m=_create_m1(hT,app,privs,wd)
    if ok: return True,m
    ok,m2=_create_m2(hT,app,privs,wd)
    if ok: return True,m2
    return False,f"M1:{m}|M2:{m2}"

def launch_svc_account(hT,app,sid,privs=False,log_cb=None):
    log=log_cb or (lambda m: None)
    exe,cl=resolve_app_and_args(app)
    hD=duplicate_token(hT,SecurityDelegation,TokenPrimary)
    if not hD: hD=duplicate_token(hT,SecurityImpersonation,TokenPrimary)
    if not hD: return False,"Dup fail"
    set_token_session_id(hD,get_current_session_id())
    pc=enable_all_privileges_on_token(hD) if privs else 0
    grant_winsta_desktop_access(sid,log); grant_winsta_desktop_access(SID_EVERYONE,log)
    env=ctypes.c_void_p(); he=False
    if userenv:
        try: he=userenv.CreateEnvironmentBlock(ctypes.byref(env),hD,False)
        except: pass
    si=STARTUPINFOW(); si.cb=ctypes.sizeof(STARTUPINFOW); si.lpDesktop="WinSta0\\Default"
    pi=PROCESS_INFORMATION(); fl=CREATE_NEW_CONSOLE|CREATE_UNICODE_ENVIRONMENT|NORMAL_PRIORITY_CLASS
    for method in [1,2,3]:
        if method==3:
            advapi32.RevertToSelf(); iok,hI=impersonate_system()
            if not iok: continue
        if cl:
            cb=ctypes.create_unicode_buffer(cl)
            if method<=2:
                if method==1: r=advapi32.CreateProcessAsUserW(hD,exe,cb,None,None,False,fl,env if he else None,None,ctypes.byref(si),ctypes.byref(pi))
                else: r=advapi32.CreateProcessWithTokenW(hD,LOGON_WITH_PROFILE,exe,cb,fl,env if he else None,None,ctypes.byref(si),ctypes.byref(pi))
            else: r=advapi32.CreateProcessAsUserW(hD,exe,cb,None,None,False,fl,env if he else None,None,ctypes.byref(si),ctypes.byref(pi))
        else:
            if method==1: r=advapi32.CreateProcessAsUserW(hD,exe,None,None,None,False,fl,env if he else None,None,ctypes.byref(si),ctypes.byref(pi))
            elif method==2: r=advapi32.CreateProcessWithTokenW(hD,LOGON_WITH_PROFILE,exe,None,fl,env if he else None,None,ctypes.byref(si),ctypes.byref(pi))
            else: r=advapi32.CreateProcessAsUserW(hD,exe,None,None,None,False,fl,env if he else None,None,ctypes.byref(si),ctypes.byref(pi))
        if method==3 and 'hI' in dir(): revert_impersonation(hI)
        if r:
            if he and env:
                try: userenv.DestroyEnvironmentBlock(env)
                except: pass
            kernel32.CloseHandle(pi.hProcess); kernel32.CloseHandle(pi.hThread); kernel32.CloseHandle(hD)
            m=f"PID: {pi.dwProcessId}"
            if privs: m+=f" | {pc} privs"
            return True,m
    if he and env:
        try: userenv.DestroyEnvironmentBlock(env)
        except: pass
    kernel32.CloseHandle(hD); return False,"All methods failed"

# ========================== Main Launch Functions ==========================

def launch_as_system(app, privs=False, log_cb=None):
    log=log_cb or (lambda m: None); enable_current_process_privileges()
    log(f"File: {get_file_type_description(app)}")
    hT=get_system_token()
    if not hT: return False,"No SYSTEM token"
    log("SYSTEM token OK")
    ok,m=launch_process(hT,app,privs); kernel32.CloseHandle(hT); return ok,m

def launch_as_ti(app, privs=False, log_cb=None):
    log=log_cb or (lambda m: None); enable_current_process_privileges()
    log(f"File: {get_file_type_description(app)}")
    iok,hI=impersonate_system()
    if not iok: return False,"SYSTEM imp failed"
    sok,_=start_ti_svc(log)
    if not sok:
        revert_impersonation(hI); hI=None
        sok,_=start_ti_sc(log)
        if not sok: return False,"TI start failed"
        iok,hI=impersonate_system()
    time.sleep(0.5)
    tp=get_pid_by_name("TrustedInstaller.exe")
    if not tp: time.sleep(1); tp=get_pid_by_name("TrustedInstaller.exe")
    if not tp: time.sleep(2); tp=get_pid_by_name("TrustedInstaller.exe")
    if not tp:
        if hI: revert_impersonation(hI)
        return False,"TI not found"
    hT=open_process_token_ex(tp)
    if hI: revert_impersonation(hI)
    if not hT: return False,"No TI token"
    ok,m=launch_process(hT,app,privs); kernel32.CloseHandle(hT); return ok,m

def launch_as_winre(app, log_cb=None, ls=None):
    log=log_cb or (lambda m: None); enable_current_process_privileges()
    log("🔥 WinRE mode"); log("━"*50)
    log(f"File: {get_file_type_description(app)}")
    log("[0/5] X: drive...")
    if ls: ls.update_status("Preparing X: drive...",5)
    xok=ensure_winre_x_drive(log,ls)
    wd=WINRE_SYSTEM32 if os.path.isdir(WINRE_SYSTEM32) else None
    log("[1/5] SYSTEM token...")
    if ls: ls.update_status("SYSTEM token...",60)
    st=get_system_token()
    if not st: return False,"No SYSTEM token"
    log("[2/5] Impersonation...")
    if ls: ls.update_status("Impersonating...",70)
    hI=duplicate_token(st,SecurityImpersonation,TokenImpersonation); kernel32.CloseHandle(st)
    if not hI: return False,"Imp failed"
    iok=advapi32.ImpersonateLoggedOnUser(hI)
    if not iok: iok=advapi32.SetThreadToken(None,hI)
    if not iok: kernel32.CloseHandle(hI); return False,"Imp failed"
    log("[3/5] TI service...")
    if ls: ls.update_status("Starting TrustedInstaller...",75)
    sok,_=start_ti_svc(log)
    if not sok:
        revert_impersonation(hI); hI=None
        sok,_=start_ti_sc(log)
        if not sok: return False,"TI failed"
        st2=get_system_token()
        if st2: hI=duplicate_token(st2,SecurityImpersonation,TokenImpersonation); kernel32.CloseHandle(st2)
        if hI: advapi32.ImpersonateLoggedOnUser(hI)
    log("[4/5] TI token...")
    if ls: ls.update_status("Getting TI token...",85)
    time.sleep(0.5)
    tp=get_pid_by_name("TrustedInstaller.exe")
    if not tp: time.sleep(1); tp=get_pid_by_name("TrustedInstaller.exe")
    if not tp: time.sleep(2); tp=get_pid_by_name("TrustedInstaller.exe")
    if not tp:
        if hI: revert_impersonation(hI)
        return False,"TI not found"
    hTI=open_process_token_ex(tp)
    if hI: revert_impersonation(hI)
    if not hTI: return False,"No TI token"
    log("[5/5] WinRE token...")
    if ls: ls.update_status("Creating WinRE process...",90)
    hW=duplicate_token(hTI,SecurityDelegation,TokenPrimary); kernel32.CloseHandle(hTI)
    if not hW: return False,"WinRE token failed"
    set_token_session_id(hW,get_current_session_id())
    pc=enable_all_privileges_on_token(hW)
    log(f"   {pc}/36 privs"); log("━"*50)
    if ls: ls.update_status("Launching...",95)
    ok,m=launch_process(hW,app,True,wd); kernel32.CloseHandle(hW)
    return (True,f"{m} | TI+SYSTEM+{pc}P | {WINRE_SYSTEM32}") if ok else (False,m)

def launch_as_ns(app, privs=False, log_cb=None):
    log=log_cb or (lambda m: None); enable_current_process_privileges()
    iok,hI=impersonate_system()
    for s in NETWORK_SERVICE_PROCESSES:
        try: subprocess.run(["sc","start",s],capture_output=True,timeout=5)
        except: pass
    time.sleep(0.5)
    hT=find_service_process_token(SID_NETWORK_SERVICE,NETWORK_SERVICE_PROCESSES,log)
    if hI: revert_impersonation(hI)
    if not hT: return False,"NS not found"
    ok,m=launch_svc_account(hT,app,SID_NETWORK_SERVICE,privs,log); kernel32.CloseHandle(hT)
    return (True,f"{m} | NETWORK SERVICE") if ok else (False,m)

def launch_as_ls(app, privs=False, log_cb=None):
    log=log_cb or (lambda m: None); enable_current_process_privileges()
    iok,hI=impersonate_system()
    for s in LOCAL_SERVICE_PROCESSES:
        try: subprocess.run(["sc","start",s],capture_output=True,timeout=5)
        except: pass
    time.sleep(0.5)
    hT=find_service_process_token(SID_LOCAL_SERVICE,LOCAL_SERVICE_PROCESSES,log)
    if hI: revert_impersonation(hI)
    if not hT: return False,"LS not found"
    ok,m=launch_svc_account(hT,app,SID_LOCAL_SERVICE,privs,log); kernel32.CloseHandle(hT)
    return (True,f"{m} | LOCAL SERVICE") if ok else (False,m)

def launch_as_admin(app, privs=False, log_cb=None):
    log=log_cb or (lambda m: None)
    if privs:
        enable_current_process_privileges()
        hT=wintypes.HANDLE()
        if advapi32.OpenProcessToken(kernel32.GetCurrentProcess(),TOKEN_ALL_ACCESS,ctypes.byref(hT)):
            ok,m=launch_process(hT,app,True); kernel32.CloseHandle(hT)
            if ok: return True,m
    ext=os.path.splitext(app)[1].lower(); sr=os.environ.get("SystemRoot","C:\\Windows")
    if ext==".exe": ret=shell32.ShellExecuteW(None,"runas",app,None,None,1)
    elif ext==".msc": ret=shell32.ShellExecuteW(None,"runas",os.path.join(sr,"System32","mmc.exe"),f'"{app}"',None,1)
    elif ext in (".bat",".cmd"): ret=shell32.ShellExecuteW(None,"runas",os.path.join(sr,"System32","cmd.exe"),f'/c "{app}"',None,1)
    elif ext==".ps1": ret=shell32.ShellExecuteW(None,"runas",os.path.join(sr,"System32","WindowsPowerShell","v1.0","powershell.exe"),f'-ExecutionPolicy Bypass -NoExit -File "{app}"',None,1)
    else: ret=shell32.ShellExecuteW(None,"runas",app,None,None,1)
    if ret and ctypes.cast(ret,ctypes.c_void_p).value>32: return True,"Admin OK"
    return False,f"Err:{ret}"

# ========================== GUI ==========================

class PrivilegeEscalatorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arasswys Runner")
        self.root.geometry("850x900")
        self.root.minsize(700, 600)
        self.root.resizable(True, True)
        self.root.configure(bg="#1a1a2e")

        self.app_path = tk.StringVar()
        self.privilege_level = tk.StringVar(value="SYSTEM")
        self.enable_all_privs = tk.BooleanVar(value=False)
        self.loading_screen = None

        self.privilege_level.trace_add("write", self._on_level_changed)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.create_widgets()
        self.center_window()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        cleanup_winre_x_drive(self.log)
        self.root.destroy()

    def center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _on_level_changed(self, *args):
        lv = self.privilege_level.get()
        if lv == "WINRE":
            self.enable_all_privs.set(False)
            self.priv_checkbox.config(state=tk.DISABLED)
            self.priv_info_label.config(
                text="     All privileges included automatically in WinRE mode.\n"
                     "     WinRE.wim → RAM disk → X: drive.\n"
                     f"     CMD/PowerShell → {WINRE_SYSTEM32}")
        else:
            self.priv_checkbox.config(state=tk.NORMAL)
            self.priv_info_label.config(
                text="     Enables ALL 36 privileges on the token:\n"
                     "     SeTcbPrivilege, SeDebugPrivilege, SeCreateTokenPrivilege,\n"
                     "     SeBackupPrivilege, SeRestorePrivilege, SeTakeOwnershipPrivilege ...\n"
                     '     → All show as "Enabled" in whoami /priv')

    def create_widgets(self):
        # TITLE
        tf = tk.Frame(self.root, bg="#16213e", pady=12)
        tf.grid(row=0, column=0, sticky="ew"); tf.columnconfigure(0, weight=1)
        tk.Label(tf, text="Arasswys Runner", font=("Segoe UI", 22, "bold"), fg="#e94560", bg="#16213e").grid(row=0, column=0)
        tk.Label(tf, text="Credits:youtube.com/@Slotshz", font=("Segoe UI", 10), fg="#a0a0a0", bg="#16213e").grid(row=1, column=0)
        tk.Label(tf, text=f"✅ Running as Administrator | PID: {os.getpid()}", font=("Segoe UI", 9, "bold"), fg="#00ff00", bg="#16213e").grid(row=2, column=0, pady=(4, 0))

        # MAIN
        container = tk.Frame(self.root, bg="#1a1a2e")
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1); container.rowconfigure(0, weight=1)
        canvas = tk.Canvas(container, bg="#1a1a2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg="#1a1a2e"); self.scroll_frame.columnconfigure(0, weight=1)
        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        cw = canvas.create_window((0, 0), window=self.scroll_frame, anchor="n")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        canvas.grid(row=0, column=0, sticky="nsew"); scrollbar.grid(row=0, column=1, sticky="ns")
        mx, my = 25, 8

        # APP
        af = tk.LabelFrame(self.scroll_frame, text="Application Selection", font=("Segoe UI", 12, "bold"),
                           fg="#00d2ff", bg="#1a1a2e", padx=15, pady=12)
        af.grid(row=0, column=0, sticky="ew", padx=mx, pady=(15, my)); af.columnconfigure(0, weight=1)
        ef = tk.Frame(af, bg="#1a1a2e"); ef.grid(row=0, column=0, sticky="ew"); ef.columnconfigure(0, weight=1)
        self.path_entry = tk.Entry(ef, textvariable=self.app_path, font=("Consolas", 11),
                                   bg="#0f3460", fg="white", insertbackground="white", relief=tk.FLAT, bd=8)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        tk.Button(ef, text="📂 Browse", font=("Segoe UI", 11, "bold"), bg="#e94560", fg="white",
                  activebackground="#c73e54", relief=tk.FLAT, padx=18, pady=6, cursor="hand2",
                  command=self.browse_file).grid(row=0, column=1)
        self.file_type_label = tk.Label(af, text="", font=("Segoe UI", 9, "italic"), fg="#ffd700", bg="#1a1a2e")
        self.file_type_label.grid(row=1, column=0, sticky="w", pady=(4, 0))
        self.app_path.trace_add("write", self._on_path_changed)

        qf = tk.Frame(af, bg="#1a1a2e"); qf.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        tk.Label(qf, text="Quick:", font=("Segoe UI", 9, "bold"), fg="#a0a0a0", bg="#1a1a2e").pack(side=tk.LEFT, padx=(0, 8))
        for n, p in [("🖥 CMD","C:\\Windows\\System32\\cmd.exe"),("⚡ PS","C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"),
                     ("🔧 Regedit","C:\\Windows\\regedit.exe"),("📝 Notepad","C:\\Windows\\System32\\notepad.exe"),
                     ("📊 TaskMgr","C:\\Windows\\System32\\taskmgr.exe"),("🖧 Services","C:\\Windows\\System32\\services.msc"),
                     ("💻 DevMgmt","C:\\Windows\\System32\\devmgmt.msc")]:
            tk.Button(qf, text=n, font=("Segoe UI", 9), bg="#0f3460", fg="white", activebackground="#1a5276",
                      relief=tk.FLAT, padx=8, pady=3, cursor="hand2",
                      command=lambda pp=p: self.app_path.set(pp)).pack(side=tk.LEFT, padx=2)

        # LEVELS
        pf = tk.LabelFrame(self.scroll_frame, text=" 🔐 Privilege Level ", font=("Segoe UI", 12, "bold"),
                           fg="#00d2ff", bg="#1a1a2e", padx=15, pady=12)
        pf.grid(row=1, column=0, sticky="ew", padx=mx, pady=my); pf.columnconfigure(0, weight=1)
        levels = [
            ("⚪ WinRE","WINRE","SYSTEM + TrustedInstaller + All Privileges + X: RAM Disk","#ffffff",True,
             f"💀 WinRE.wim → RAM → X: | CMD/PS → {WINRE_SYSTEM32}"),
            ("🔴 TrustedInstaller","TRUSTEDINSTALLER","NT SERVICE\\TrustedInstaller","#ff4444",False,None),
            ("🟠 SYSTEM","SYSTEM","NT AUTHORITY\\SYSTEM","#ff8800",False,None),
            ("🌐 Network Service","NETWORKSERVICE","NT AUTHORITY\\NETWORK SERVICE","#00bfff",False,"💡 SID: S-1-5-20"),
            ("🏠 Local Service","LOCALSERVICE","NT AUTHORITY\\LOCAL SERVICE","#00cc66",False,"💡 SID: S-1-5-19"),
            ("🟡 Administrator","ADMIN","Elevated admin token","#ffcc00",False,None),
        ]
        for i,(text,val,desc,color,iw,extra) in enumerate(levels):
            if iw:
                card=tk.Frame(pf,bg="#1a1a1a",highlightbackground="#ffffff",highlightthickness=2,padx=12,pady=8); cbg="#1a1a1a"
            else:
                card=tk.Frame(pf,bg="#0f3460",padx=12,pady=8); cbg="#0f3460"
            card.grid(row=i,column=0,sticky="ew",pady=3); card.columnconfigure(0,weight=1)
            tk.Radiobutton(card,text=text,variable=self.privilege_level,value=val,font=("Segoe UI",12,"bold"),
                           fg=color,bg=cbg,selectcolor="#1a1a2e",activebackground=cbg,cursor="hand2").grid(row=0,column=0,sticky="w")
            tk.Label(card,text=f"     {desc}",font=("Segoe UI",9),fg="#808080",bg=cbg).grid(row=1,column=0,sticky="w")
            if extra:
                tk.Label(card,text=f"     {extra}",font=("Segoe UI",9,"bold" if iw else "italic"),
                         fg=color if iw else "#888888",bg=cbg).grid(row=2,column=0,sticky="w")

        # EXTRA
        of = tk.LabelFrame(self.scroll_frame, text=" ⚡ Extra Options ", font=("Segoe UI", 12, "bold"),
                           fg="#00d2ff", bg="#1a1a2e", padx=15, pady=12)
        of.grid(row=2, column=0, sticky="ew", padx=mx, pady=my); of.columnconfigure(0, weight=1)
        oc = tk.Frame(of, bg="#0f3460", padx=12, pady=10)
        oc.grid(row=0, column=0, sticky="ew"); oc.columnconfigure(0, weight=1)
        self.priv_checkbox = tk.Checkbutton(oc, text="🔓 Enable All Privileges", variable=self.enable_all_privs,
                                            font=("Segoe UI", 12, "bold"), fg="#ffd700", bg="#0f3460",
                                            selectcolor="#1a1a2e", activebackground="#0f3460",
                                            disabledforeground="#555555", cursor="hand2")
        self.priv_checkbox.grid(row=0, column=0, sticky="w")
        self.priv_info_label = tk.Label(oc, text=(
            "     Enables ALL 36 privileges on the token:\n"
            "     SeTcbPrivilege, SeDebugPrivilege, SeCreateTokenPrivilege,\n"
            "     SeBackupPrivilege, SeRestorePrivilege, SeTakeOwnershipPrivilege ...\n"
            '     → All show as "Enabled" in whoami /priv'),
            font=("Segoe UI", 9), fg="#808080", bg="#0f3460", justify=tk.LEFT)
        self.priv_info_label.grid(row=1, column=0, sticky="w")

        # FILE TYPES
        ftf = tk.LabelFrame(self.scroll_frame, text=" 📄 Supported File Types ", font=("Segoe UI", 12, "bold"),
                            fg="#00d2ff", bg="#1a1a2e", padx=15, pady=8)
        ftf.grid(row=3, column=0, sticky="ew", padx=mx, pady=my); ftf.columnconfigure(0, weight=1)
        tk.Label(ftf, text="  .exe .msc .bat .cmd .ps1 .vbs .py .cpl .reg .msi",
                 font=("Consolas", 10), fg="#a0a0a0", bg="#1a1a2e").grid(row=0, column=0, sticky="w")

        # LAUNCH
        bf = tk.Frame(self.scroll_frame, bg="#1a1a2e")
        bf.grid(row=4, column=0, sticky="ew", padx=mx, pady=(15, 8)); bf.columnconfigure(0, weight=1)
        self.launch_btn = tk.Button(bf, text="🚀  LAUNCH", font=("Segoe UI", 18, "bold"),
                                    bg="#e94560", fg="white", activebackground="#c73e54", relief=tk.FLAT,
                                    padx=30, pady=12, cursor="hand2", command=self.launch)
        self.launch_btn.grid(row=0, column=0, sticky="ew")
        self.launch_btn.bind("<Enter>", lambda e: self.launch_btn.config(bg="#ff5a7a"))
        self.launch_btn.bind("<Leave>", lambda e: self.launch_btn.config(bg="#e94560"))

        # LOG
        lf = tk.LabelFrame(self.scroll_frame, text=" 📋 Operation Log ", font=("Segoe UI", 12, "bold"),
                           fg="#00d2ff", bg="#1a1a2e", padx=10, pady=10)
        lf.grid(row=5, column=0, sticky="nsew", padx=mx, pady=(5, 15))
        lf.columnconfigure(0, weight=1); lf.rowconfigure(0, weight=1)
        self.scroll_frame.rowconfigure(5, weight=1)

        lc = tk.Frame(lf, bg="#0a0a1a"); lc.grid(row=0, column=0, sticky="nsew")
        lc.columnconfigure(0, weight=1); lc.rowconfigure(0, weight=1)
        self.log_text = tk.Text(lc, height=10, font=("Consolas", 10), bg="#0a0a1a", fg="#00ff00",
                                insertbackground="#00ff00", relief=tk.FLAT, bd=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        ls = ttk.Scrollbar(lc, orient="vertical", command=self.log_text.yview)
        ls.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=ls.set, state=tk.DISABLED)

        self.log("Program started ✅")
        self.log(f"Python {sys.version.split()[0]}")
        self.log("WinRE: WinRE.wim → RAM → X:\\Windows\\System32")
        self.log("Select app → Choose level → LAUNCH\n")

        # STATUS
        sb = tk.Frame(self.root, bg="#0f3460", pady=5)
        sb.grid(row=2, column=0, sticky="ew"); sb.columnconfigure(0, weight=1)
        self.status_var = tk.StringVar(value="✅ Ready")
        tk.Label(sb, textvariable=self.status_var, font=("Consolas", 10), fg="#a0a0a0",
                 bg="#0f3460", anchor=tk.W).grid(row=0, column=0, padx=10, sticky="w")

    def _on_path_changed(self, *args):
        p = self.app_path.get().strip()
        if p and os.path.splitext(p)[1]:
            self.file_type_label.config(text=f"📄 {get_file_type_description(p)}")
        else:
            self.file_type_label.config(text="")

    def log(self, msg):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        try: self.root.update_idletasks()
        except: pass

    def browse_file(self):
        fp = filedialog.askopenfilename(title="Select Application", filetypes=[
            ("All Supported", "*.exe;*.msc;*.bat;*.cmd;*.ps1;*.vbs;*.py;*.cpl;*.reg;*.msi"),("All", "*.*")])
        if fp: self.app_path.set(fp); self.log(f"Selected: {fp}")

    def launch(self):
        ap = self.app_path.get().strip()
        if not ap: messagebox.showwarning("Warning", "Select an application!"); return
        if not os.path.exists(ap): messagebox.showerror("Error", f"Not found:\n{ap}"); return

        lv = self.privilege_level.get()
        ep = self.enable_all_privs.get()
        names = {"SYSTEM":"SYSTEM","TRUSTEDINSTALLER":"TrustedInstaller","ADMIN":"Administrator",
                 "WINRE":"WinRE","NETWORKSERVICE":"Network Service","LOCALSERVICE":"Local Service"}
        ln = names.get(lv, lv)
        ps = " (SYSTEM+TI+AllPrivs+X:)" if lv=="WINRE" else (" +AllPrivs" if ep else "")

        self.log(f"━━━ {ln}{ps} ━━━")
        self.log(f"Target: {os.path.basename(ap)}")
        self.status_var.set(f"⏳ {ln}...")
        self.launch_btn.config(state=tk.DISABLED, bg="#555555", text="⏳ Processing...")
        self.root.update()

        try:
            if lv == "WINRE":
                self.loading_screen = LoadingScreen(self.root)
                self.loading_screen.show("Preparing WinRE Environment...")
                def winre_work():
                    try:
                        ok, msg = launch_as_winre(ap, self.log, self.loading_screen)
                        self.root.after(0, lambda: self._done_winre(ok, msg, ln))
                    except Exception as e:
                        self.root.after(0, lambda: self._done_winre(False, str(e), ln))
                threading.Thread(target=winre_work, daemon=True).start()
                return

            elif lv=="SYSTEM": ok,msg=launch_as_system(ap,ep,self.log)
            elif lv=="TRUSTEDINSTALLER": ok,msg=launch_as_ti(ap,ep,self.log)
            elif lv=="ADMIN": ok,msg=launch_as_admin(ap,ep,self.log)
            elif lv=="NETWORKSERVICE": ok,msg=launch_as_ns(ap,ep,self.log)
            elif lv=="LOCALSERVICE": ok,msg=launch_as_ls(ap,ep,self.log)
            else: ok,msg=False,"Unknown"

            if ok: self.log(f"✅ {msg}"); self.status_var.set(f"✅ {ln}!")
            else: self.log(f"❌ {msg}"); self.status_var.set("❌ Error!"); messagebox.showerror("Error",f"❌ {msg}")
        except Exception as e:
            self.log(f"❌ {e}"); self.status_var.set("❌ Error!"); messagebox.showerror("Error",str(e))
        finally:
            self.launch_btn.config(state=tk.NORMAL, bg="#e94560", text="🚀  LAUNCH"); self.log("")

    def _done_winre(self, ok, msg, ln):
        if self.loading_screen: self.loading_screen.close(); self.loading_screen=None
        if ok: self.log(f"✅ {msg}"); self.status_var.set(f"✅ {ln}!")
        else: self.log(f"❌ {msg}"); self.status_var.set("❌ Error!"); messagebox.showerror("Error",f"❌ {msg}")
        self.launch_btn.config(state=tk.NORMAL, bg="#e94560", text="🚀  LAUNCH"); self.log("")

    def run(self):
        self.root.mainloop()

# ========================== MAIN ==========================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        print("="*60)
        print("  Arasswys Runner - CLI")
        print("="*60)
        print("\n1. WinRE  2. SYSTEM  3. TrustedInstaller")
        print("4. Network Service  5. Local Service  6. Admin\n")
        ch=input("(1-6): ").strip()
        ap=input("App (empty=cmd): ").strip() or "C:\\Windows\\System32\\cmd.exe"
        pv=True if ch=="1" else input("All privs? (y/n): ").strip().lower()=="y"
        print(); cb=lambda m: print(f"  {m}")
        if ch=="1": ok,m=launch_as_winre(ap,cb)
        elif ch=="2": ok,m=launch_as_system(ap,pv,cb)
        elif ch=="3": ok,m=launch_as_ti(ap,pv,cb)
        elif ch=="4": ok,m=launch_as_ns(ap,pv,cb)
        elif ch=="5": ok,m=launch_as_ls(ap,pv,cb)
        elif ch=="6": ok,m=launch_as_admin(ap,pv,cb)
        else: print("Invalid!"); sys.exit(1)
        print(f"\n[{'+'if ok else '-'}] {m}")
        if ch=="1": input("\nEnter to unmount..."); cleanup_winre_x_drive(cb)
    else:
        if not show_license_agreement():
            sys.exit(0)
        PrivilegeEscalatorGUI().run()