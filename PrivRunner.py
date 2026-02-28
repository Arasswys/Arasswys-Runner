import ctypes
import ctypes.wintypes as wintypes
import subprocess
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import time
import threading

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
advapi32.AdjustTokenPrivileges.argtypes = [
    wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TOKEN_PRIVILEGES),
    wintypes.DWORD, ctypes.POINTER(TOKEN_PRIVILEGES), ctypes.POINTER(wintypes.DWORD)
]

advapi32.DuplicateTokenEx.restype = wintypes.BOOL
advapi32.DuplicateTokenEx.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)
]

advapi32.SetTokenInformation.restype = wintypes.BOOL
advapi32.SetTokenInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD]

advapi32.GetTokenInformation.restype = wintypes.BOOL
advapi32.GetTokenInformation.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
]

advapi32.ImpersonateLoggedOnUser.restype = wintypes.BOOL
advapi32.ImpersonateLoggedOnUser.argtypes = [wintypes.HANDLE]

advapi32.SetThreadToken.restype = wintypes.BOOL
advapi32.SetThreadToken.argtypes = [ctypes.c_void_p, wintypes.HANDLE]

advapi32.RevertToSelf.restype = wintypes.BOOL
advapi32.RevertToSelf.argtypes = []

advapi32.CreateProcessAsUserW.restype = wintypes.BOOL
advapi32.CreateProcessAsUserW.argtypes = [
    wintypes.HANDLE, wintypes.LPCWSTR, wintypes.LPWSTR,
    ctypes.c_void_p, ctypes.c_void_p,
    wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
    ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)
]

advapi32.CreateProcessWithTokenW.restype = wintypes.BOOL
advapi32.CreateProcessWithTokenW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPWSTR,
    wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
    ctypes.POINTER(STARTUPINFOW), ctypes.POINTER(PROCESS_INFORMATION)
]

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
user32.GetUserObjectSecurity.argtypes = [
    wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD),
    ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
]

shell32.ShellExecuteW.restype = wintypes.HINSTANCE
shell32.ShellExecuteW.argtypes = [
    wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR,
    wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_int
]

if userenv:
    userenv.CreateEnvironmentBlock.restype = wintypes.BOOL
    userenv.CreateEnvironmentBlock.argtypes = [ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.BOOL]
    userenv.DestroyEnvironmentBlock.restype = wintypes.BOOL
    userenv.DestroyEnvironmentBlock.argtypes = [ctypes.c_void_p]

# ========================== All Privilege Names ==========================

ALL_PRIVILEGES = [
    "SeAssignPrimaryTokenPrivilege", "SeAuditPrivilege", "SeBackupPrivilege",
    "SeChangeNotifyPrivilege", "SeCreateGlobalPrivilege", "SeCreatePagefilePrivilege",
    "SeCreatePermanentPrivilege", "SeCreateSymbolicLinkPrivilege",
    "SeCreateTokenPrivilege", "SeDebugPrivilege",
    "SeDelegateSessionUserImpersonatePrivilege", "SeEnableDelegationPrivilege",
    "SeImpersonatePrivilege", "SeIncreaseBasePriorityPrivilege",
    "SeIncreaseQuotaPrivilege", "SeIncreaseWorkingSetPrivilege",
    "SeLoadDriverPrivilege", "SeLockMemoryPrivilege", "SeMachineAccountPrivilege",
    "SeManageVolumePrivilege", "SeProfileSingleProcessPrivilege",
    "SeRelabelPrivilege", "SeRemoteShutdownPrivilege", "SeRestorePrivilege",
    "SeSecurityPrivilege", "SeShutdownPrivilege", "SeSyncAgentPrivilege",
    "SeSystemEnvironmentPrivilege", "SeSystemProfilePrivilege",
    "SeSystemtimePrivilege", "SeTakeOwnershipPrivilege", "SeTcbPrivilege",
    "SeTimeZonePrivilege", "SeTrustedCredManAccessPrivilege",
    "SeUndockPrivilege", "SeUnsolicitedInputPrivilege",
]

NETWORK_SERVICE_PROCESSES = [
    "nlasvc", "dnscache", "LanmanWorkstation", "CryptSvc",
    "TermService", "Dhcp", "NlaSvc", "WinHttpAutoProxySvc",
]

LOCAL_SERVICE_PROCESSES = [
    "EventLog", "nsi", "W32Time", "WinHttpAutoProxySvc",
    "AudioSrv", "fdPHost", "FontCache", "TimeBrokerSvc", "SCardSvr",
]

SID_NETWORK_SERVICE = "S-1-5-20"
SID_LOCAL_SERVICE = "S-1-5-19"
SID_LOCAL_SYSTEM = "S-1-5-18"
SID_EVERYONE = "S-1-1-0"

# ========================== FILE TYPE RESOLVER ==========================

def resolve_app_and_args(app_path):
    """
    Resolves the actual executable and command line arguments based on file extension.
    Returns (exe_path, command_line) tuple.
    
    .exe  → (app_path, None)
    .msc  → (mmc.exe, "mmc.exe app_path")
    .bat  → (cmd.exe, 'cmd.exe /c "app_path"')
    .cmd  → (cmd.exe, 'cmd.exe /c "app_path"')
    .ps1  → (powershell.exe, 'powershell.exe -ExecutionPolicy Bypass -File "app_path"')
    .vbs  → (cscript.exe, 'cscript.exe //nologo "app_path"')
    .js   → (cscript.exe, 'cscript.exe //nologo "app_path"')
    .py   → (python.exe, 'python.exe "app_path"')
    .cpl  → (control.exe, 'control.exe "app_path"')
    other → (cmd.exe, 'cmd.exe /c "app_path"')
    """
    ext = os.path.splitext(app_path)[1].lower()
    sys32 = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")

    if ext == ".exe":
        return app_path, None

    elif ext == ".msc":
        mmc_path = os.path.join(sys32, "mmc.exe")
        cmd_line = f'"{mmc_path}" "{app_path}"'
        return mmc_path, cmd_line

    elif ext in (".bat", ".cmd"):
        cmd_path = os.path.join(sys32, "cmd.exe")
        cmd_line = f'"{cmd_path}" /c "{app_path}"'
        return cmd_path, cmd_line

    elif ext == ".ps1":
        ps_path = os.path.join(sys32, "WindowsPowerShell", "v1.0", "powershell.exe")
        if not os.path.exists(ps_path):
            ps_path = "powershell.exe"
        cmd_line = f'"{ps_path}" -ExecutionPolicy Bypass -NoExit -File "{app_path}"'
        return ps_path, cmd_line

    elif ext in (".vbs", ".vbe"):
        cscript_path = os.path.join(sys32, "cscript.exe")
        cmd_line = f'"{cscript_path}" //nologo "{app_path}"'
        return cscript_path, cmd_line

    elif ext in (".js", ".jse", ".wsf"):
        cscript_path = os.path.join(sys32, "cscript.exe")
        cmd_line = f'"{cscript_path}" //nologo "{app_path}"'
        return cscript_path, cmd_line

    elif ext == ".py":
        py_path = sys.executable if sys.executable else "python.exe"
        cmd_line = f'"{py_path}" "{app_path}"'
        return py_path, cmd_line

    elif ext == ".cpl":
        control_path = os.path.join(sys32, "control.exe")
        cmd_line = f'"{control_path}" "{app_path}"'
        return control_path, cmd_line

    elif ext == ".reg":
        regedit_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "regedit.exe")
        cmd_line = f'"{regedit_path}" "{app_path}"'
        return regedit_path, cmd_line

    elif ext in (".msi", ".msp"):
        msiexec_path = os.path.join(sys32, "msiexec.exe")
        cmd_line = f'"{msiexec_path}" /i "{app_path}"'
        return msiexec_path, cmd_line

    else:
        # Fallback: use cmd /c to let Windows handle the association
        cmd_path = os.path.join(sys32, "cmd.exe")
        cmd_line = f'"{cmd_path}" /c start "" "{app_path}"'
        return cmd_path, cmd_line


def get_file_type_description(app_path):
    """Returns a human-readable description of how the file will be launched."""
    ext = os.path.splitext(app_path)[1].lower()
    descriptions = {
        ".exe": "Direct executable",
        ".msc": "MMC Snap-in → launched via mmc.exe",
        ".bat": "Batch script → launched via cmd.exe",
        ".cmd": "Command script → launched via cmd.exe",
        ".ps1": "PowerShell script → launched via powershell.exe",
        ".vbs": "VBScript → launched via cscript.exe",
        ".vbe": "VBScript Encoded → launched via cscript.exe",
        ".js": "JScript → launched via cscript.exe",
        ".jse": "JScript Encoded → launched via cscript.exe",
        ".wsf": "Windows Script File → launched via cscript.exe",
        ".py": "Python script → launched via python.exe",
        ".cpl": "Control Panel → launched via control.exe",
        ".reg": "Registry file → launched via regedit.exe",
        ".msi": "Installer package → launched via msiexec.exe",
        ".msp": "Installer patch → launched via msiexec.exe",
    }
    return descriptions.get(ext, f"Unknown type ({ext}) → launched via cmd.exe")


# ========================== Helper Functions ==========================

def enable_privilege(priv_name):
    hToken = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(
        kernel32.GetCurrentProcess(), TOKEN_ALL_ACCESS, ctypes.byref(hToken)
    ):
        return False
    luid = LUID()
    if not advapi32.LookupPrivilegeValueW(None, priv_name, ctypes.byref(luid)):
        kernel32.CloseHandle(hToken)
        return False
    tp = TOKEN_PRIVILEGES()
    tp.PrivilegeCount = 1
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
    result = advapi32.AdjustTokenPrivileges(hToken, False, ctypes.byref(tp), ctypes.sizeof(tp), None, None)
    error = ctypes.get_last_error()
    kernel32.CloseHandle(hToken)
    return result and error == 0


def enable_current_process_privileges():
    for priv in ["SeDebugPrivilege", "SeImpersonatePrivilege",
                 "SeAssignPrimaryTokenPrivilege", "SeIncreaseQuotaPrivilege",
                 "SeTcbPrivilege", "SeBackupPrivilege", "SeRestorePrivilege"]:
        enable_privilege(priv)


def get_pid_by_name(process_name):
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(INVALID_HANDLE_VALUE).value or snapshot is None:
        return None
    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    pids = []
    if kernel32.Process32FirstW(snapshot, ctypes.byref(pe)):
        while True:
            if pe.szExeFile.lower() == process_name.lower():
                pids.append(pe.th32ProcessID)
            if not kernel32.Process32NextW(snapshot, ctypes.byref(pe)):
                break
    kernel32.CloseHandle(snapshot)
    return pids[0] if pids else None


def get_all_pids_by_name(process_name):
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(INVALID_HANDLE_VALUE).value or snapshot is None:
        return []
    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    pids = []
    if kernel32.Process32FirstW(snapshot, ctypes.byref(pe)):
        while True:
            if pe.szExeFile.lower() == process_name.lower():
                pids.append(pe.th32ProcessID)
            if not kernel32.Process32NextW(snapshot, ctypes.byref(pe)):
                break
    kernel32.CloseHandle(snapshot)
    return pids


def open_process_token_ex(pid, desired_access=TOKEN_ALL_ACCESS):
    access_levels = [
        PROCESS_QUERY_INFORMATION,
        PROCESS_QUERY_LIMITED_INFORMATION,
        MAXIMUM_ALLOWED,
    ]
    for access in access_levels:
        hProcess = kernel32.OpenProcess(access, False, pid)
        if hProcess and hProcess != wintypes.HANDLE(0).value:
            hToken = wintypes.HANDLE()
            token_access_levels = [
                desired_access,
                TOKEN_ALL_ACCESS,
                TOKEN_DUPLICATE | TOKEN_QUERY | TOKEN_IMPERSONATE,
                TOKEN_DUPLICATE | TOKEN_QUERY,
                MAXIMUM_ALLOWED,
            ]
            for ta in token_access_levels:
                if advapi32.OpenProcessToken(hProcess, ta, ctypes.byref(hToken)):
                    kernel32.CloseHandle(hProcess)
                    return hToken
            kernel32.CloseHandle(hProcess)
    return None


def get_token_user_sid_string(hToken):
    buf_size = wintypes.DWORD(0)
    advapi32.GetTokenInformation(hToken, 1, None, 0, ctypes.byref(buf_size))
    if buf_size.value == 0:
        return None
    buf = ctypes.create_string_buffer(buf_size.value)
    if not advapi32.GetTokenInformation(hToken, 1, buf, buf_size.value, ctypes.byref(buf_size)):
        return None
    sid_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
    sid_string = wintypes.LPWSTR()
    if advapi32.ConvertSidToStringSidW(sid_ptr, ctypes.byref(sid_string)):
        result = sid_string.value
        kernel32.LocalFree(ctypes.cast(sid_string, wintypes.HANDLE))
        return result
    return None


def get_system_token():
    enable_current_process_privileges()
    for proc_name in ["winlogon.exe", "lsass.exe", "services.exe", "svchost.exe"]:
        pid = get_pid_by_name(proc_name)
        if pid:
            hToken = open_process_token_ex(pid)
            if hToken:
                return hToken
    return None


def find_service_process_token(target_sid, service_names, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    enable_current_process_privileges()
    log(f"   Target SID: {target_sid}")

    for svc_name in service_names:
        try:
            result = subprocess.run(["sc", "query", svc_name], capture_output=True, text=True, timeout=5)
            if "RUNNING" not in result.stdout:
                subprocess.run(["sc", "start", svc_name], capture_output=True, text=True, timeout=10)
                time.sleep(0.3)
        except:
            pass

    svchost_pids = get_all_pids_by_name("svchost.exe")
    log(f"   Found {len(svchost_pids)} svchost.exe processes, scanning...")

    for pid in svchost_pids:
        hToken = open_process_token_ex(pid)
        if not hToken:
            continue
        sid_str = get_token_user_sid_string(hToken)
        if sid_str and sid_str == target_sid:
            log(f"   ✅ Matching process found! PID: {pid} SID: {sid_str}")
            return hToken
        kernel32.CloseHandle(hToken)

    log("   Not found in svchost, scanning all processes...")
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == wintypes.HANDLE(INVALID_HANDLE_VALUE).value or snapshot is None:
        return None

    pe = PROCESSENTRY32W()
    pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    checked = set(svchost_pids)

    if kernel32.Process32FirstW(snapshot, ctypes.byref(pe)):
        while True:
            pid = pe.th32ProcessID
            if pid not in checked and pid > 4:
                hToken = open_process_token_ex(pid)
                if hToken:
                    sid_str = get_token_user_sid_string(hToken)
                    if sid_str and sid_str == target_sid:
                        log(f"   ✅ Matching process found! PID: {pid} ({pe.szExeFile}) SID: {sid_str}")
                        kernel32.CloseHandle(snapshot)
                        return hToken
                    kernel32.CloseHandle(hToken)
            if not kernel32.Process32NextW(snapshot, ctypes.byref(pe)):
                break

    kernel32.CloseHandle(snapshot)
    return None


def duplicate_token(hToken, imp_level=SecurityDelegation, token_type=TokenPrimary):
    hNewToken = wintypes.HANDLE()
    result = advapi32.DuplicateTokenEx(
        hToken, MAXIMUM_ALLOWED, None, imp_level, token_type, ctypes.byref(hNewToken)
    )
    if result:
        return hNewToken
    result = advapi32.DuplicateTokenEx(
        hToken, MAXIMUM_ALLOWED, None, SecurityImpersonation, token_type, ctypes.byref(hNewToken)
    )
    return hNewToken if result else None


def enable_all_privileges_on_token(hToken):
    count = 0
    for priv_name in ALL_PRIVILEGES:
        luid = LUID()
        if advapi32.LookupPrivilegeValueW(None, priv_name, ctypes.byref(luid)):
            tp = TOKEN_PRIVILEGES()
            tp.PrivilegeCount = 1
            tp.Privileges[0].Luid = luid
            tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED | SE_PRIVILEGE_ENABLED_BY_DEFAULT
            if advapi32.AdjustTokenPrivileges(hToken, False, ctypes.byref(tp), ctypes.sizeof(tp), None, None):
                if ctypes.get_last_error() == 0:
                    count += 1
    return count


def set_token_session_id(hToken, session_id):
    TokenSessionId = 12
    sid = wintypes.DWORD(session_id)
    return advapi32.SetTokenInformation(hToken, TokenSessionId, ctypes.byref(sid), ctypes.sizeof(sid))


def get_current_session_id():
    session_id = wintypes.DWORD()
    kernel32.ProcessIdToSessionId(kernel32.GetCurrentProcessId(), ctypes.byref(session_id))
    return session_id.value


def grant_winsta_desktop_access(sid_string, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    pSid = ctypes.c_void_p()
    if not advapi32.ConvertStringSidToSidW(sid_string, ctypes.byref(pSid)):
        log(f"   ⚠ Could not convert SID: {sid_string}")
        return False

    success_count = 0

    hWinSta = user32.OpenWindowStationW("WinSta0", False, READ_CONTROL | WRITE_DAC)
    if hWinSta:
        if _add_ace_to_object(hWinSta, pSid, WINSTA_ALL_ACCESS | GENERIC_ALL):
            log("   ✅ WinSta0 access granted")
            success_count += 1
        else:
            log("   ⚠ WinSta0 access failed")
        user32.CloseWindowStation(hWinSta)
    else:
        log(f"   ⚠ Could not open WinSta0: {ctypes.get_last_error()}")

    hDesktop = user32.OpenDesktopW("Default", 0, False, READ_CONTROL | WRITE_DAC | DESKTOP_ALL_ACCESS)
    if hDesktop:
        if _add_ace_to_object(hDesktop, pSid, DESKTOP_ALL_ACCESS | GENERIC_ALL):
            log("   ✅ Desktop\\Default access granted")
            success_count += 1
        else:
            log("   ⚠ Desktop\\Default access failed")
        user32.CloseDesktop(hDesktop)
    else:
        log(f"   ⚠ Could not open Desktop: {ctypes.get_last_error()}")

    kernel32.LocalFree(pSid)
    return success_count > 0


def _add_ace_to_object(hObject, pSid, access_mask):
    sid_length = advapi32.GetLengthSid(pSid)
    acl_size = 1024 + sid_length * 2
    new_acl = ctypes.create_string_buffer(acl_size)

    if not advapi32.InitializeAcl(new_acl, acl_size, ACL_REVISION):
        return False

    everyone_sid = ctypes.c_void_p()
    if advapi32.ConvertStringSidToSidW(SID_EVERYONE, ctypes.byref(everyone_sid)):
        advapi32.AddAccessAllowedAce(new_acl, ACL_REVISION, access_mask, everyone_sid)
        kernel32.LocalFree(everyone_sid)

    advapi32.AddAccessAllowedAce(new_acl, ACL_REVISION, access_mask, pSid)

    system_sid = ctypes.c_void_p()
    if advapi32.ConvertStringSidToSidW(SID_LOCAL_SYSTEM, ctypes.byref(system_sid)):
        advapi32.AddAccessAllowedAce(new_acl, ACL_REVISION, access_mask, system_sid)
        kernel32.LocalFree(system_sid)

    SECURITY_DESCRIPTOR_MIN_LENGTH = 40
    new_sd = ctypes.create_string_buffer(SECURITY_DESCRIPTOR_MIN_LENGTH)
    advapi32.InitializeSecurityDescriptor(new_sd, 1)
    advapi32.SetSecurityDescriptorDacl(new_sd, True, new_acl, False)

    si = wintypes.DWORD(DACL_SECURITY_INFORMATION)
    result = user32.SetUserObjectSecurity(hObject, ctypes.byref(si), new_sd)
    return bool(result)


def impersonate_system():
    system_token = get_system_token()
    if not system_token:
        return False, None
    hImpToken = duplicate_token(system_token, SecurityImpersonation, TokenImpersonation)
    kernel32.CloseHandle(system_token)
    if not hImpToken:
        return False, None
    if advapi32.ImpersonateLoggedOnUser(hImpToken):
        return True, hImpToken
    else:
        if advapi32.SetThreadToken(None, hImpToken):
            return True, hImpToken
        kernel32.CloseHandle(hImpToken)
        return False, None


def revert_impersonation(hImpToken):
    advapi32.RevertToSelf()
    if hImpToken:
        kernel32.CloseHandle(hImpToken)


def start_trustedinstaller_service_impersonated(log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    hSCManager = advapi32.OpenSCManagerW(None, None, SC_MANAGER_ALL_ACCESS)
    if not hSCManager:
        hSCManager = advapi32.OpenSCManagerW(None, None, SC_MANAGER_CONNECT)
    if not hSCManager:
        return False, f"Could not open SCManager! Error: {ctypes.get_last_error()}"

    hService = advapi32.OpenServiceW(hSCManager, "TrustedInstaller", SERVICE_ALL_ACCESS)
    if not hService:
        hService = advapi32.OpenServiceW(hSCManager, "TrustedInstaller", SERVICE_START | SERVICE_QUERY_STATUS)
    if not hService:
        error = ctypes.get_last_error()
        advapi32.CloseServiceHandle(hSCManager)
        return False, f"Could not open TrustedInstaller service! Error: {error}"

    status = SERVICE_STATUS()
    advapi32.QueryServiceStatus(hService, ctypes.byref(status))

    if status.dwCurrentState == SERVICE_RUNNING:
        advapi32.CloseServiceHandle(hService)
        advapi32.CloseServiceHandle(hSCManager)
        return True, "TrustedInstaller is already running."

    start_result = advapi32.StartServiceW(hService, 0, None)
    start_error = ctypes.get_last_error()

    if not start_result and start_error != 1056:
        advapi32.CloseServiceHandle(hService)
        advapi32.CloseServiceHandle(hSCManager)
        return False, f"Could not start service! Error: {start_error}"

    for i in range(60):
        advapi32.QueryServiceStatus(hService, ctypes.byref(status))
        if status.dwCurrentState == SERVICE_RUNNING:
            break
        time.sleep(0.3)

    running = status.dwCurrentState == SERVICE_RUNNING
    advapi32.CloseServiceHandle(hService)
    advapi32.CloseServiceHandle(hSCManager)
    return (True, "TrustedInstaller service started.") if running else (False, "Service did not start in time!")


def start_trustedinstaller_via_sc_command(log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)
    try:
        result = subprocess.run(["sc", "query", "TrustedInstaller"], capture_output=True, text=True, timeout=10)
        if "RUNNING" in result.stdout:
            return True, "TrustedInstaller is already running (sc query)."

        result = subprocess.run(["sc", "start", "TrustedInstaller"], capture_output=True, text=True, timeout=30)
        if result.returncode == 0 or "RUNNING" in result.stdout or "START_PENDING" in result.stdout:
            for i in range(30):
                check = subprocess.run(["sc", "query", "TrustedInstaller"], capture_output=True, text=True, timeout=10)
                if "RUNNING" in check.stdout:
                    return True, "TrustedInstaller service started (sc.exe)."
                time.sleep(0.5)
            return False, "Service did not reach RUNNING state."
        else:
            return False, f"sc start failed: {result.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return False, "sc.exe timeout!"
    except Exception as e:
        return False, f"sc.exe error: {e}"


# ========================== Process Creation (with file type support) ==========================

def create_process_with_token_method1(hToken, app_path, enable_all_privs=False):
    exe_path, cmd_line = resolve_app_and_args(app_path)

    hDupToken = duplicate_token(hToken, SecurityDelegation, TokenPrimary)
    if not hDupToken:
        return False, "Token duplication failed!"

    set_token_session_id(hDupToken, get_current_session_id())
    priv_count = 0
    if enable_all_privs:
        priv_count = enable_all_privileges_on_token(hDupToken)

    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = "WinSta0\\Default"
    pi = PROCESS_INFORMATION()
    flags = CREATE_NEW_CONSOLE | CREATE_UNICODE_ENVIRONMENT | NORMAL_PRIORITY_CLASS

    env = ctypes.c_void_p()
    has_env = False
    if userenv:
        try:
            has_env = userenv.CreateEnvironmentBlock(ctypes.byref(env), hDupToken, False)
        except:
            pass

    # If cmd_line is set, use it; otherwise pass exe_path as lpApplicationName
    if cmd_line:
        cmd_buf = ctypes.create_unicode_buffer(cmd_line)
        result = advapi32.CreateProcessAsUserW(
            hDupToken, exe_path, cmd_buf, None, None, False,
            flags, env if has_env else None, None, ctypes.byref(si), ctypes.byref(pi)
        )
    else:
        result = advapi32.CreateProcessAsUserW(
            hDupToken, exe_path, None, None, None, False,
            flags, env if has_env else None, None, ctypes.byref(si), ctypes.byref(pi)
        )
    error = ctypes.get_last_error()

    if has_env and env:
        try:
            userenv.DestroyEnvironmentBlock(env)
        except:
            pass

    if result:
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(hDupToken)
        msg = f"PID: {pi.dwProcessId}"
        if enable_all_privs:
            msg += f" | {priv_count} privileges enabled"
        return True, msg
    else:
        kernel32.CloseHandle(hDupToken)
        return False, f"CreateProcessAsUserW error: {error}"


def create_process_with_token_method2(hToken, app_path, enable_all_privs=False):
    exe_path, cmd_line = resolve_app_and_args(app_path)

    hDupToken = duplicate_token(hToken, SecurityImpersonation, TokenPrimary)
    if not hDupToken:
        return False, "Token duplication failed!"

    set_token_session_id(hDupToken, get_current_session_id())
    priv_count = 0
    if enable_all_privs:
        priv_count = enable_all_privileges_on_token(hDupToken)

    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = "WinSta0\\Default"
    pi = PROCESS_INFORMATION()
    flags = CREATE_NEW_CONSOLE | CREATE_UNICODE_ENVIRONMENT

    if cmd_line:
        cmd_buf = ctypes.create_unicode_buffer(cmd_line)
        result = advapi32.CreateProcessWithTokenW(
            hDupToken, LOGON_WITH_PROFILE, exe_path, cmd_buf,
            flags, None, None, ctypes.byref(si), ctypes.byref(pi)
        )
    else:
        result = advapi32.CreateProcessWithTokenW(
            hDupToken, LOGON_WITH_PROFILE, exe_path, None,
            flags, None, None, ctypes.byref(si), ctypes.byref(pi)
        )
    error = ctypes.get_last_error()

    if result:
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(hDupToken)
        msg = f"PID: {pi.dwProcessId}"
        if enable_all_privs:
            msg += f" | {priv_count} privileges enabled"
        return True, msg
    else:
        kernel32.CloseHandle(hDupToken)
        return False, f"CreateProcessWithTokenW error: {error}"


def launch_process(hToken, app_path, enable_all_privs=False):
    success, msg = create_process_with_token_method1(hToken, app_path, enable_all_privs)
    if success:
        return True, msg
    success, msg2 = create_process_with_token_method2(hToken, app_path, enable_all_privs)
    if success:
        return True, msg2
    return False, f"Method1: {msg} | Method2: {msg2}"


def launch_process_service_account(hToken, app_path, sid_string, enable_all_privs=False, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    exe_path, cmd_line = resolve_app_and_args(app_path)

    hDupToken = duplicate_token(hToken, SecurityDelegation, TokenPrimary)
    if not hDupToken:
        hDupToken = duplicate_token(hToken, SecurityImpersonation, TokenPrimary)
    if not hDupToken:
        return False, "Token duplication failed!"

    session_id = get_current_session_id()
    set_token_session_id(hDupToken, session_id)
    log(f"   Session ID: {session_id}")

    priv_count = 0
    if enable_all_privs:
        priv_count = enable_all_privileges_on_token(hDupToken)
        log(f"   {priv_count} privileges enabled")

    log("   Setting WinSta0/Desktop access permissions...")
    grant_winsta_desktop_access(sid_string, log)
    grant_winsta_desktop_access(SID_EVERYONE, log)

    env = ctypes.c_void_p()
    has_env = False
    if userenv:
        try:
            has_env = userenv.CreateEnvironmentBlock(ctypes.byref(env), hDupToken, False)
            if has_env:
                log("   ✅ Environment block created")
        except:
            pass

    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = "WinSta0\\Default"
    pi = PROCESS_INFORMATION()
    flags = CREATE_NEW_CONSOLE | CREATE_UNICODE_ENVIRONMENT | NORMAL_PRIORITY_CLASS

    # Method 1
    log("   Method 1: Trying CreateProcessAsUserW...")
    if cmd_line:
        cmd_buf = ctypes.create_unicode_buffer(cmd_line)
        result = advapi32.CreateProcessAsUserW(
            hDupToken, exe_path, cmd_buf, None, None, False,
            flags, env if has_env else None, None,
            ctypes.byref(si), ctypes.byref(pi)
        )
    else:
        result = advapi32.CreateProcessAsUserW(
            hDupToken, exe_path, None, None, None, False,
            flags, env if has_env else None, None,
            ctypes.byref(si), ctypes.byref(pi)
        )
    error1 = ctypes.get_last_error()

    if result:
        if has_env and env:
            try: userenv.DestroyEnvironmentBlock(env)
            except: pass
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(hDupToken)
        msg = f"PID: {pi.dwProcessId}"
        if enable_all_privs:
            msg += f" | {priv_count} privileges"
        return True, msg

    log(f"   Method 1 failed (error: {error1})")

    # Method 2
    log("   Method 2: Trying CreateProcessWithTokenW...")
    if cmd_line:
        cmd_buf2 = ctypes.create_unicode_buffer(cmd_line)
        result = advapi32.CreateProcessWithTokenW(
            hDupToken, LOGON_WITH_PROFILE, exe_path, cmd_buf2,
            flags, env if has_env else None, None,
            ctypes.byref(si), ctypes.byref(pi)
        )
    else:
        result = advapi32.CreateProcessWithTokenW(
            hDupToken, LOGON_WITH_PROFILE, exe_path, None,
            flags, env if has_env else None, None,
            ctypes.byref(si), ctypes.byref(pi)
        )
    error2 = ctypes.get_last_error()

    if result:
        if has_env and env:
            try: userenv.DestroyEnvironmentBlock(env)
            except: pass
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(hDupToken)
        msg = f"PID: {pi.dwProcessId}"
        if enable_all_privs:
            msg += f" | {priv_count} privileges"
        return True, msg

    log(f"   Method 2 failed (error: {error2})")

    # Method 3: SYSTEM impersonate + retry
    log("   Method 3: Trying SYSTEM impersonate + CreateProcessAsUser...")
    advapi32.RevertToSelf()

    imp_ok, hImpToken = impersonate_system()
    error3 = 0
    if imp_ok:
        si2 = STARTUPINFOW()
        si2.cb = ctypes.sizeof(STARTUPINFOW)
        si2.lpDesktop = "WinSta0\\Default"
        pi2 = PROCESS_INFORMATION()

        env2 = ctypes.c_void_p()
        has_env2 = False
        if userenv:
            try:
                has_env2 = userenv.CreateEnvironmentBlock(ctypes.byref(env2), hDupToken, False)
            except:
                pass

        if cmd_line:
            cmd_buf3 = ctypes.create_unicode_buffer(cmd_line)
            result = advapi32.CreateProcessAsUserW(
                hDupToken, exe_path, cmd_buf3, None, None, False,
                flags, env2 if has_env2 else None, None,
                ctypes.byref(si2), ctypes.byref(pi2)
            )
        else:
            result = advapi32.CreateProcessAsUserW(
                hDupToken, exe_path, None, None, None, False,
                flags, env2 if has_env2 else None, None,
                ctypes.byref(si2), ctypes.byref(pi2)
            )
        error3 = ctypes.get_last_error()

        if has_env2 and env2:
            try: userenv.DestroyEnvironmentBlock(env2)
            except: pass

        revert_impersonation(hImpToken)

        if result:
            if has_env and env:
                try: userenv.DestroyEnvironmentBlock(env)
                except: pass
            kernel32.CloseHandle(pi2.hProcess)
            kernel32.CloseHandle(pi2.hThread)
            kernel32.CloseHandle(hDupToken)
            msg = f"PID: {pi2.dwProcessId}"
            if enable_all_privs:
                msg += f" | {priv_count} privileges"
            return True, msg

        log(f"   Method 3 failed (error: {error3})")
    else:
        log("   SYSTEM impersonate failed")

    if has_env and env:
        try: userenv.DestroyEnvironmentBlock(env)
        except: pass

    kernel32.CloseHandle(hDupToken)
    return False, f"All methods failed! Error1:{error1} Error2:{error2} Error3:{error3}"


# ========================== Main Launch Functions ==========================

def launch_as_system(app_path, enable_all_privs=False, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    enable_current_process_privileges()
    log("SeDebugPrivilege enabled")

    file_desc = get_file_type_description(app_path)
    log(f"File type: {file_desc}")

    hToken = get_system_token()
    if not hToken:
        return False, "Could not obtain SYSTEM token!"

    log("SYSTEM token obtained (winlogon.exe)")
    success, msg = launch_process(hToken, app_path, enable_all_privs)
    kernel32.CloseHandle(hToken)
    return success, msg


def launch_as_trustedinstaller(app_path, enable_all_privs=False, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    enable_current_process_privileges()
    log("Current process privileges enabled")

    file_desc = get_file_type_description(app_path)
    log(f"File type: {file_desc}")

    log("Impersonating as SYSTEM...")
    imp_success, hImpToken = impersonate_system()
    if not imp_success:
        return False, "SYSTEM impersonation failed!"

    log("✅ SYSTEM impersonation successful")

    log("Starting TrustedInstaller service (API)...")
    svc_success, svc_msg = start_trustedinstaller_service_impersonated(log)
    log(f"   Result: {svc_msg}")

    if not svc_success:
        log("API failed, trying sc.exe...")
        revert_impersonation(hImpToken)
        hImpToken = None
        svc_success, svc_msg = start_trustedinstaller_via_sc_command(log)
        if not svc_success:
            return False, f"Could not start TrustedInstaller: {svc_msg}"
        imp_success, hImpToken = impersonate_system()

    time.sleep(0.5)
    ti_pid = get_pid_by_name("TrustedInstaller.exe")
    if not ti_pid:
        time.sleep(1.0)
        ti_pid = get_pid_by_name("TrustedInstaller.exe")
    if not ti_pid:
        time.sleep(2.0)
        ti_pid = get_pid_by_name("TrustedInstaller.exe")

    if not ti_pid:
        if hImpToken:
            revert_impersonation(hImpToken)
        return False, "TrustedInstaller.exe not found!"

    log(f"TrustedInstaller.exe PID: {ti_pid}")
    hToken = open_process_token_ex(ti_pid)

    if hImpToken:
        revert_impersonation(hImpToken)

    if not hToken:
        return False, "Could not obtain TrustedInstaller token!"

    log("✅ TrustedInstaller token obtained")
    success, msg = launch_process(hToken, app_path, enable_all_privs)
    kernel32.CloseHandle(hToken)
    return success, msg


def launch_as_root(app_path, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    enable_current_process_privileges()
    log("🔥 ROOT mode — Combining all privilege layers")
    log("━" * 50)

    file_desc = get_file_type_description(app_path)
    log(f"File type: {file_desc}")

    exe_path, cmd_line = resolve_app_and_args(app_path)

    log("[1/5] Obtaining SYSTEM token...")
    system_token = get_system_token()
    if not system_token:
        return False, "Could not obtain SYSTEM token!"
    log("   ✅ SYSTEM token obtained")

    log("[2/5] Performing SYSTEM impersonation...")
    hImpToken = duplicate_token(system_token, SecurityImpersonation, TokenImpersonation)
    kernel32.CloseHandle(system_token)

    if not hImpToken:
        return False, "Could not create SYSTEM impersonation token!"

    imp_ok = advapi32.ImpersonateLoggedOnUser(hImpToken)
    if not imp_ok:
        imp_ok = advapi32.SetThreadToken(None, hImpToken)
    if not imp_ok:
        kernel32.CloseHandle(hImpToken)
        return False, "SYSTEM impersonation failed!"
    log("   ✅ Impersonated as SYSTEM")

    log("[3/5] Starting TrustedInstaller service...")
    svc_success, svc_msg = start_trustedinstaller_service_impersonated(log)

    if not svc_success:
        revert_impersonation(hImpToken)
        hImpToken = None
        svc_success, svc_msg = start_trustedinstaller_via_sc_command(log)
        if not svc_success:
            return False, f"Could not start TrustedInstaller: {svc_msg}"
        system_token = get_system_token()
        if system_token:
            hImpToken = duplicate_token(system_token, SecurityImpersonation, TokenImpersonation)
            kernel32.CloseHandle(system_token)
            if hImpToken:
                advapi32.ImpersonateLoggedOnUser(hImpToken)

    log("[4/5] Obtaining TrustedInstaller token...")
    time.sleep(0.5)
    ti_pid = get_pid_by_name("TrustedInstaller.exe")
    if not ti_pid:
        time.sleep(1.0)
        ti_pid = get_pid_by_name("TrustedInstaller.exe")
    if not ti_pid:
        time.sleep(2.0)
        ti_pid = get_pid_by_name("TrustedInstaller.exe")

    if not ti_pid:
        if hImpToken:
            revert_impersonation(hImpToken)
        return False, "TrustedInstaller.exe not found!"

    hTIToken = open_process_token_ex(ti_pid)
    if hImpToken:
        revert_impersonation(hImpToken)

    if not hTIToken:
        return False, "Could not obtain TrustedInstaller token!"

    log("[5/5] Creating ROOT token...")
    hRootToken = duplicate_token(hTIToken, SecurityDelegation, TokenPrimary)
    kernel32.CloseHandle(hTIToken)

    if not hRootToken:
        return False, "Could not create ROOT token!"

    set_token_session_id(hRootToken, get_current_session_id())
    priv_count = enable_all_privileges_on_token(hRootToken)
    log(f"   → {priv_count}/36 privileges enabled")
    log("━" * 50)

    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(STARTUPINFOW)
    si.lpDesktop = "WinSta0\\Default"
    pi = PROCESS_INFORMATION()
    flags = CREATE_NEW_CONSOLE | CREATE_UNICODE_ENVIRONMENT | NORMAL_PRIORITY_CLASS

    env = ctypes.c_void_p()
    has_env = False
    if userenv:
        try:
            has_env = userenv.CreateEnvironmentBlock(ctypes.byref(env), hRootToken, False)
        except:
            pass

    if cmd_line:
        cmd_buf = ctypes.create_unicode_buffer(cmd_line)
        result = advapi32.CreateProcessAsUserW(
            hRootToken, exe_path, cmd_buf, None, None, False,
            flags, env if has_env else None, None, ctypes.byref(si), ctypes.byref(pi)
        )
    else:
        result = advapi32.CreateProcessAsUserW(
            hRootToken, exe_path, None, None, None, False,
            flags, env if has_env else None, None, ctypes.byref(si), ctypes.byref(pi)
        )
    error1 = ctypes.get_last_error()
    error2 = 0

    if not result:
        if cmd_line:
            cmd_buf2 = ctypes.create_unicode_buffer(cmd_line)
            result = advapi32.CreateProcessWithTokenW(
                hRootToken, LOGON_WITH_PROFILE, exe_path, cmd_buf2,
                CREATE_NEW_CONSOLE | CREATE_UNICODE_ENVIRONMENT, None, None,
                ctypes.byref(si), ctypes.byref(pi)
            )
        else:
            result = advapi32.CreateProcessWithTokenW(
                hRootToken, LOGON_WITH_PROFILE, exe_path, None,
                CREATE_NEW_CONSOLE | CREATE_UNICODE_ENVIRONMENT, None, None,
                ctypes.byref(si), ctypes.byref(pi)
            )
        error2 = ctypes.get_last_error()

    if has_env and env:
        try: userenv.DestroyEnvironmentBlock(env)
        except: pass

    if result:
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)
        kernel32.CloseHandle(hRootToken)
        return True, f"PID: {pi.dwProcessId} | TrustedInstaller + SYSTEM + {priv_count} Privileges"
    else:
        kernel32.CloseHandle(hRootToken)
        return False, f"Could not create ROOT process! Error1: {error1}, Error2: {error2}"


def launch_as_network_service(app_path, enable_all_privs=False, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    enable_current_process_privileges()
    log("🌐 NETWORK SERVICE mode")
    log("━" * 50)

    file_desc = get_file_type_description(app_path)
    log(f"File type: {file_desc}")

    log("[1/4] Performing SYSTEM impersonation...")
    imp_success, hImpToken = impersonate_system()
    if not imp_success:
        log("   ⚠ Impersonation failed, scanning directly...")
    else:
        log("   ✅ SYSTEM impersonation successful")

    log("[2/4] Searching for Network Service (S-1-5-20) process...")
    for svc in NETWORK_SERVICE_PROCESSES:
        try:
            subprocess.run(["sc", "start", svc], capture_output=True, timeout=5)
        except:
            pass
    time.sleep(0.5)

    hToken = find_service_process_token(SID_NETWORK_SERVICE, NETWORK_SERVICE_PROCESSES, log)

    if hImpToken:
        revert_impersonation(hImpToken)

    if not hToken:
        return False, "Network Service token not found!"

    log("[3/4] ✅ Network Service token obtained")
    log("[4/4] Creating process (setting WinSta/Desktop permissions)...")

    success, msg = launch_process_service_account(
        hToken, app_path, SID_NETWORK_SERVICE, enable_all_privs, log
    )
    kernel32.CloseHandle(hToken)

    if success:
        return True, f"{msg} | NT AUTHORITY\\NETWORK SERVICE"
    return False, msg


def launch_as_local_service(app_path, enable_all_privs=False, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    enable_current_process_privileges()
    log("🏠 LOCAL SERVICE mode")
    log("━" * 50)

    file_desc = get_file_type_description(app_path)
    log(f"File type: {file_desc}")

    log("[1/4] Performing SYSTEM impersonation...")
    imp_success, hImpToken = impersonate_system()
    if not imp_success:
        log("   ⚠ Impersonation failed, scanning directly...")
    else:
        log("   ✅ SYSTEM impersonation successful")

    log("[2/4] Searching for Local Service (S-1-5-19) process...")
    for svc in LOCAL_SERVICE_PROCESSES:
        try:
            subprocess.run(["sc", "start", svc], capture_output=True, timeout=5)
        except:
            pass
    time.sleep(0.5)

    hToken = find_service_process_token(SID_LOCAL_SERVICE, LOCAL_SERVICE_PROCESSES, log)

    if hImpToken:
        revert_impersonation(hImpToken)

    if not hToken:
        return False, "Local Service token not found!"

    log("[3/4] ✅ Local Service token obtained")
    log("[4/4] Creating process (setting WinSta/Desktop permissions)...")

    success, msg = launch_process_service_account(
        hToken, app_path, SID_LOCAL_SERVICE, enable_all_privs, log
    )
    kernel32.CloseHandle(hToken)

    if success:
        return True, f"{msg} | NT AUTHORITY\\LOCAL SERVICE"
    return False, msg


def launch_as_admin(app_path, enable_all_privs=False, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    file_desc = get_file_type_description(app_path)
    log(f"File type: {file_desc}")

    if enable_all_privs:
        enable_current_process_privileges()
        hToken = wintypes.HANDLE()
        if advapi32.OpenProcessToken(
            kernel32.GetCurrentProcess(), TOKEN_ALL_ACCESS, ctypes.byref(hToken)
        ):
            log("Admin token obtained, enabling all privileges...")
            success, msg = launch_process(hToken, app_path, True)
            kernel32.CloseHandle(hToken)
            if success:
                return True, msg

    ext = os.path.splitext(app_path)[1].lower()
    if ext == ".exe":
        ret = shell32.ShellExecuteW(None, "runas", app_path, None, None, 1)
    elif ext == ".msc":
        mmc = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "mmc.exe")
        ret = shell32.ShellExecuteW(None, "runas", mmc, f'"{app_path}"', None, 1)
    elif ext in (".bat", ".cmd"):
        cmd = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "cmd.exe")
        ret = shell32.ShellExecuteW(None, "runas", cmd, f'/c "{app_path}"', None, 1)
    elif ext == ".ps1":
        ps = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32",
                          "WindowsPowerShell", "v1.0", "powershell.exe")
        ret = shell32.ShellExecuteW(None, "runas", ps,
                                    f'-ExecutionPolicy Bypass -NoExit -File "{app_path}"', None, 1)
    else:
        ret = shell32.ShellExecuteW(None, "runas", app_path, None, None, 1)

    if ret and ctypes.cast(ret, ctypes.c_void_p).value > 32:
        return True, "Application launched as admin!"
    else:
        return False, f"Launch failed! Error: {ret}"


# ========================== GUI ==========================

class PrivilegeEscalatorGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Arasswys Runner")
        self.root.geometry("820x880")
        self.root.minsize(660, 700)
        self.root.configure(bg="#1a1a2e")

        self.app_path = tk.StringVar()
        self.privilege_level = tk.StringVar(value="SYSTEM")
        self.enable_all_privs = tk.BooleanVar(value=False)

        self.privilege_level.trace_add("write", self._on_level_changed)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.create_widgets()
        self.center_window()

    def center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _on_level_changed(self, *args):
        level = self.privilege_level.get()
        if level == "ROOT":
            self.enable_all_privs.set(False)
            self.priv_checkbox.config(state=tk.DISABLED)
            self.priv_info_label.config(
                text="     All privileges are automatically included in ROOT mode.\n"
                     "     This option cannot be used with ROOT."
            )
        else:
            self.priv_checkbox.config(state=tk.NORMAL)
            self.priv_info_label.config(
                text="     Enables ALL privileges on the token:\n"
                     "     SeTcbPrivilege, SeDebugPrivilege, SeCreateTokenPrivilege,\n"
                     "     SeBackupPrivilege, SeRestorePrivilege, SeTakeOwnershipPrivilege ...\n"
                     '     → All show as "Enabled" in whoami /priv'
            )

    def create_widgets(self):
        # ========== TITLE ==========
        title_frame = tk.Frame(self.root, bg="#16213e", pady=12)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.columnconfigure(0, weight=1)

        tk.Label(title_frame, text="Arasswys Runner",
                 font=("Segoe UI", 22, "bold"), fg="#e94560", bg="#16213e").grid(row=0, column=0)
        tk.Label(title_frame,
                 text="Credits:youtube.com/@Slotshz",
                 font=("Segoe UI", 10), fg="#a0a0a0", bg="#16213e").grid(row=1, column=0)
        tk.Label(title_frame, text=f"✅ Running as Administrator | PID: {os.getpid()}",
                 font=("Segoe UI", 9, "bold"), fg="#00ff00", bg="#16213e").grid(row=2, column=0, pady=(4, 0))

        # ========== MAIN AREA ==========
        container = tk.Frame(self.root, bg="#1a1a2e")
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(container, bg="#1a1a2e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        self.scroll_frame = tk.Frame(canvas, bg="#1a1a2e")
        self.scroll_frame.columnconfigure(0, weight=1)

        self.scroll_frame.bind("<Configure>",
                               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        cw = canvas.create_window((0, 0), window=self.scroll_frame, anchor="n")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        def _mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _mousewheel)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        mx = 25
        my = 8

        # ========== APPLICATION SELECTION ==========
        app_frame = tk.LabelFrame(self.scroll_frame, text="Application Selection",
                                  font=("Segoe UI", 12, "bold"), fg="#00d2ff", bg="#1a1a2e",
                                  padx=15, pady=12)
        app_frame.grid(row=0, column=0, sticky="ew", padx=mx, pady=(15, my))
        app_frame.columnconfigure(0, weight=1)

        ef = tk.Frame(app_frame, bg="#1a1a2e")
        ef.grid(row=0, column=0, sticky="ew")
        ef.columnconfigure(0, weight=1)

        self.path_entry = tk.Entry(ef, textvariable=self.app_path, font=("Consolas", 11),
                                   bg="#0f3460", fg="white", insertbackground="white",
                                   relief=tk.FLAT, bd=8)
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        tk.Button(ef, text="📂 Browse", font=("Segoe UI", 11, "bold"),
                  bg="#e94560", fg="white", activebackground="#c73e54",
                  relief=tk.FLAT, padx=18, pady=6, cursor="hand2",
                  command=self.browse_file).grid(row=0, column=1)

        # File type info label
        self.file_type_label = tk.Label(app_frame, text="", font=("Segoe UI", 9, "italic"),
                                        fg="#ffd700", bg="#1a1a2e")
        self.file_type_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.app_path.trace_add("write", self._on_path_changed)

        qf = tk.Frame(app_frame, bg="#1a1a2e")
        qf.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        tk.Label(qf, text="Quick:", font=("Segoe UI", 9, "bold"),
                 fg="#a0a0a0", bg="#1a1a2e").pack(side=tk.LEFT, padx=(0, 8))

        for name, path in [
            ("🖥 CMD", "C:\\Windows\\System32\\cmd.exe"),
            ("⚡ PowerShell", "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"),
            ("🔧 Regedit", "C:\\Windows\\regedit.exe"),
            ("📝 Notepad", "C:\\Windows\\System32\\notepad.exe"),
            ("📊 TaskMgr", "C:\\Windows\\System32\\taskmgr.exe"),
            ("🖧 Services", "C:\\Windows\\System32\\services.msc"),
            ("💻 DevMgmt", "C:\\Windows\\System32\\devmgmt.msc"),
        ]:
            tk.Button(qf, text=name, font=("Segoe UI", 9), bg="#0f3460", fg="white",
                      activebackground="#1a5276", relief=tk.FLAT, padx=8, pady=3,
                      cursor="hand2", command=lambda p=path: self.app_path.set(p)
                      ).pack(side=tk.LEFT, padx=2)

        # ========== PRIVILEGE LEVEL ==========
        pf = tk.LabelFrame(self.scroll_frame, text=" 🔐 Privilege Level ",
                           font=("Segoe UI", 12, "bold"), fg="#00d2ff", bg="#1a1a2e",
                           padx=15, pady=12)
        pf.grid(row=1, column=0, sticky="ew", padx=mx, pady=my)
        pf.columnconfigure(0, weight=1)

        levels = [
            ("⚫ Root", "ROOT",
             "SYSTEM + TrustedInstaller + All 36 Privileges — Absolute highest authority",
             "#ff00ff", True,
             "💀 whoami → TrustedInstaller | whoami /priv → 36/36 Enabled"),
            ("🔴 TrustedInstaller", "TRUSTEDINSTALLER",
             "NT SERVICE\\TrustedInstaller — Owner of system files",
             "#ff4444", False, None),
            ("🟠 SYSTEM", "SYSTEM",
             "NT AUTHORITY\\SYSTEM — Full access to hardware, services and registry",
             "#ff8800", False, None),
            ("🌐 Network Service", "NETWORKSERVICE",
             "NT AUTHORITY\\NETWORK SERVICE — Network service authority, limited local access",
             "#00bfff", False,
             "💡 whoami → nt authority\\network service | SID: S-1-5-20"),
            ("🏠 Local Service", "LOCALSERVICE",
             "NT AUTHORITY\\LOCAL SERVICE — Local service authority, minimum access",
             "#00cc66", False,
             "💡 whoami → nt authority\\local service | SID: S-1-5-19"),
            ("🟡 Administrator", "ADMIN",
             "Elevated admin token — Standard administrator privileges",
             "#ffcc00", False, None),
        ]

        for i, (text, value, desc, color, is_root, extra_info) in enumerate(levels):
            if is_root:
                card = tk.Frame(pf, bg="#1a0030", highlightbackground="#ff00ff",
                               highlightthickness=2, padx=12, pady=8)
                card_bg = "#1a0030"
            else:
                card = tk.Frame(pf, bg="#0f3460", padx=12, pady=8)
                card_bg = "#0f3460"

            card.grid(row=i, column=0, sticky="ew", pady=3)
            card.columnconfigure(0, weight=1)

            tk.Radiobutton(card, text=text, variable=self.privilege_level, value=value,
                           font=("Segoe UI", 12, "bold"), fg=color, bg=card_bg,
                           selectcolor="#1a1a2e", activebackground=card_bg,
                           cursor="hand2").grid(row=0, column=0, sticky="w")

            tk.Label(card, text=f"     {desc}", font=("Segoe UI", 9),
                     fg="#808080", bg=card_bg).grid(row=1, column=0, sticky="w")

            if extra_info:
                info_color = color if is_root else "#888888"
                tk.Label(card, text=f"     {extra_info}",
                         font=("Segoe UI", 9, "bold" if is_root else "italic"),
                         fg=info_color, bg=card_bg).grid(row=2, column=0, sticky="w")

        # ========== EXTRA OPTIONS ==========
        of = tk.LabelFrame(self.scroll_frame, text=" ⚡ Extra Options ",
                           font=("Segoe UI", 12, "bold"), fg="#00d2ff", bg="#1a1a2e",
                           padx=15, pady=12)
        of.grid(row=2, column=0, sticky="ew", padx=mx, pady=my)
        of.columnconfigure(0, weight=1)

        oc = tk.Frame(of, bg="#0f3460", padx=12, pady=10)
        oc.grid(row=0, column=0, sticky="ew")
        oc.columnconfigure(0, weight=1)

        self.priv_checkbox = tk.Checkbutton(
            oc, text="🔓 Enable All Privileges",
            variable=self.enable_all_privs,
            font=("Segoe UI", 12, "bold"), fg="#ffd700", bg="#0f3460",
            selectcolor="#1a1a2e", activebackground="#0f3460",
            disabledforeground="#555555", cursor="hand2"
        )
        self.priv_checkbox.grid(row=0, column=0, sticky="w")

        self.priv_info_label = tk.Label(oc, text=(
            "     Enables ALL 36 privileges on the token:\n"
            "     SeTcbPrivilege, SeDebugPrivilege, SeCreateTokenPrivilege,\n"
            "     SeBackupPrivilege, SeRestorePrivilege, SeTakeOwnershipPrivilege ...\n"
            '     → All show as "Enabled" in whoami /priv'
        ), font=("Segoe UI", 9), fg="#808080", bg="#0f3460", justify=tk.LEFT)
        self.priv_info_label.grid(row=1, column=0, sticky="w")

        # ========== SUPPORTED TYPES INFO ==========
        tf = tk.LabelFrame(self.scroll_frame, text=" 📄 Supported File Types ",
                           font=("Segoe UI", 12, "bold"), fg="#00d2ff", bg="#1a1a2e",
                           padx=15, pady=8)
        tf.grid(row=3, column=0, sticky="ew", padx=mx, pady=my)
        tf.columnconfigure(0, weight=1)

        types_text = (
            "  .exe → Direct execution    |    .msc → via mmc.exe    |    .bat/.cmd → via cmd.exe\n"
            "  .ps1 → via powershell.exe   |    .vbs → via cscript.exe    |    .py → via python.exe\n"
            "  .cpl → via control.exe    |    .reg → via regedit.exe    |    .msi → via msiexec.exe"
        )
        tk.Label(tf, text=types_text, font=("Consolas", 9), fg="#a0a0a0", bg="#1a1a2e",
                 justify=tk.LEFT).grid(row=0, column=0, sticky="w")

        # ========== LAUNCH BUTTON ==========
        bf = tk.Frame(self.scroll_frame, bg="#1a1a2e")
        bf.grid(row=4, column=0, sticky="ew", padx=mx, pady=(15, 8))
        bf.columnconfigure(0, weight=1)

        self.launch_btn = tk.Button(bf, text="🚀  LAUNCH",
                                    font=("Segoe UI", 18, "bold"), bg="#e94560", fg="white",
                                    activebackground="#c73e54", relief=tk.FLAT,
                                    padx=30, pady=12, cursor="hand2",
                                    command=self.launch)
        self.launch_btn.grid(row=0, column=0, sticky="ew")
        self.launch_btn.bind("<Enter>", lambda e: self.launch_btn.config(bg="#ff5a7a"))
        self.launch_btn.bind("<Leave>", lambda e: self.launch_btn.config(bg="#e94560"))

        # ========== LOG AREA ==========
        lf = tk.LabelFrame(self.scroll_frame, text=" 📋 Operation Log ",
                           font=("Segoe UI", 12, "bold"), fg="#00d2ff", bg="#1a1a2e",
                           padx=10, pady=10)
        lf.grid(row=5, column=0, sticky="ew", padx=mx, pady=(5, 15))
        lf.columnconfigure(0, weight=1)

        log_container = tk.Frame(lf, bg="#0a0a1a")
        log_container.grid(row=0, column=0, sticky="ew")
        log_container.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_container, height=10, font=("Consolas", 10),
                                bg="#0a0a1a", fg="#00ff00", insertbackground="#00ff00",
                                relief=tk.FLAT, bd=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky="ew")

        log_scroll = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set, state=tk.DISABLED)

        self.log("Program started — Administrator privileges active ✅")
        self.log(f"Python {sys.version.split()[0]} | Windows {os.name}")
        self.log("Supported: .exe .msc .bat .cmd .ps1 .vbs .py .cpl .reg .msi")
        self.log("Select an application → Choose privilege level → LAUNCH\n")

        # ========== STATUS BAR ==========
        sb = tk.Frame(self.root, bg="#0f3460", pady=5)
        sb.grid(row=2, column=0, sticky="ew")
        sb.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="✅ Ready")
        tk.Label(sb, textvariable=self.status_var, font=("Consolas", 10),
                 fg="#a0a0a0", bg="#0f3460", anchor=tk.W).grid(row=0, column=0, padx=10, sticky="w")

    def _on_path_changed(self, *args):
        path = self.app_path.get().strip()
        if path and os.path.splitext(path)[1]:
            desc = get_file_type_description(path)
            self.file_type_label.config(text=f"📄 {desc}")
        else:
            self.file_type_label.config(text="")

    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def browse_file(self):
        fp = filedialog.askopenfilename(
            title="Select Application",
            filetypes=[
                ("All Supported", "*.exe;*.msc;*.bat;*.cmd;*.ps1;*.vbs;*.py;*.cpl;*.reg;*.msi"),
                ("Executables", "*.exe"),
                ("MMC Snap-ins", "*.msc"),
                ("Batch Scripts", "*.bat;*.cmd"),
                ("PowerShell Scripts", "*.ps1"),
                ("VBScript", "*.vbs"),
                ("Python Scripts", "*.py"),
                ("Control Panel", "*.cpl"),
                ("Registry Files", "*.reg"),
                ("Installers", "*.msi"),
                ("All Files", "*.*"),
            ]
        )
        if fp:
            self.app_path.set(fp)
            self.log(f"Selected: {fp}")

    def launch(self):
        app_path = self.app_path.get().strip()
        if not app_path:
            messagebox.showwarning("Warning", "Please select an application!")
            return
        if not os.path.exists(app_path):
            messagebox.showerror("Error", f"File not found:\n{app_path}")
            return

        level = self.privilege_level.get()
        enable_privs = self.enable_all_privs.get()
        level_names = {
            "SYSTEM": "SYSTEM", "TRUSTEDINSTALLER": "TrustedInstaller",
            "ADMIN": "Administrator", "ROOT": "Root",
            "NETWORKSERVICE": "Network Service", "LOCALSERVICE": "Local Service",
        }
        level_name = level_names.get(level, level)

        if level == "ROOT":
            priv_str = " (SYSTEM + TrustedInstaller + All Privileges)"
        else:
            priv_str = " + All Privileges" if enable_privs else ""

        self.log(f"━━━ Launching as {level_name}{priv_str} ━━━")
        self.log(f"Target: {os.path.basename(app_path)}")

        # Show resolved exe info
        exe_path, cmd_line = resolve_app_and_args(app_path)
        if cmd_line:
            self.log(f"Resolved: {os.path.basename(exe_path)} → {cmd_line}")

        self.status_var.set(f"⏳ Launching as {level_name}...")
        self.launch_btn.config(state=tk.DISABLED, bg="#555555", text="⏳ Processing...")
        self.root.update()

        try:
            if level == "SYSTEM":
                success, msg = launch_as_system(app_path, enable_privs, self.log)
            elif level == "TRUSTEDINSTALLER":
                success, msg = launch_as_trustedinstaller(app_path, enable_privs, self.log)
            elif level == "ADMIN":
                success, msg = launch_as_admin(app_path, enable_privs, self.log)
            elif level == "ROOT":
                success, msg = launch_as_root(app_path, self.log)
            elif level == "NETWORKSERVICE":
                success, msg = launch_as_network_service(app_path, enable_privs, self.log)
            elif level == "LOCALSERVICE":
                success, msg = launch_as_local_service(app_path, enable_privs, self.log)
            else:
                success, msg = False, "Unknown level!"

            if success:
                self.log(f"✅ SUCCESS: {msg}")
                self.status_var.set(f"✅ Launched as {level_name}!")
            else:
                self.log(f"❌ FAILED: {msg}")
                self.status_var.set("❌ Error occurred!")
                messagebox.showerror("Error", f"❌ {msg}")

        except Exception as e:
            self.log(f"❌ EXCEPTION: {e}")
            self.status_var.set("❌ Error!")
            messagebox.showerror("Error", str(e))
        finally:
            self.launch_btn.config(state=tk.NORMAL, bg="#e94560", text="🚀  LAUNCH")
            self.log("")

    def run(self):
        self.root.mainloop()


# ========================== MAIN ==========================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        print("=" * 60)
        print("  🛡️ Privilege Escalator - CLI")
        print("  ✅ Administrator privileges active")
        print("  📄 Supports: .exe .msc .bat .cmd .ps1 .vbs .py .cpl .reg .msi")
        print("=" * 60)
        print("\n1. Root (SYSTEM+TI+AllPrivs)")
        print("2. SYSTEM")
        print("3. TrustedInstaller")
        print("4. Network Service")
        print("5. Local Service")
        print("6. Administrator\n")

        choice = input("Selection (1-6): ").strip()
        app = input("Application (empty=cmd): ").strip() or "C:\\Windows\\System32\\cmd.exe"

        if os.path.exists(app):
            print(f"  File type: {get_file_type_description(app)}")
            exe, cmd = resolve_app_and_args(app)
            if cmd:
                print(f"  Will run: {cmd}")

        if choice != "1":
            privs = input("All privileges? (y/n): ").strip().lower() == "y"
        else:
            privs = True

        print()
        cb = lambda m: print(f"  {m}")

        if choice == "1":
            ok, msg = launch_as_root(app, cb)
        elif choice == "2":
            ok, msg = launch_as_system(app, privs, cb)
        elif choice == "3":
            ok, msg = launch_as_trustedinstaller(app, privs, cb)
        elif choice == "4":
            ok, msg = launch_as_network_service(app, privs, cb)
        elif choice == "5":
            ok, msg = launch_as_local_service(app, privs, cb)
        elif choice == "6":
            ok, msg = launch_as_admin(app, privs, cb)
        else:
            print("Invalid!"); sys.exit(1)

        print(f"\n[{'+'if ok else '-'}] {msg}")
    else:
        PrivilegeEscalatorGUI().run()