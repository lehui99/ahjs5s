try:
    import _winreg as winreg
except ImportError:
    import winreg
import ctypes

INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
    r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
    0, winreg.KEY_ALL_ACCESS)

INTERNET_OPTION_REFRESH = 37
INTERNET_OPTION_SETTINGS_CHANGED = 39

internet_set_option = ctypes.windll.Wininet.InternetSetOptionW

def set_regkey(name, value):
    _, reg_type = winreg.QueryValueEx(INTERNET_SETTINGS, name)
    winreg.SetValueEx(INTERNET_SETTINGS, name, 0, reg_type, value)

def refersh_settings():
    internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)
    internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)

def set_proxy(proxy_server):  # proxy_server = u'X.X.X.X:8080'
    set_regkey('ProxyServer', proxy_server)
    # set_regkey('ProxyOverride', u'*.local;<local>')  # Bypass the proxy for localhost
    set_regkey('ProxyEnable', 1)
    refersh_settings()

def unset_proxy():
    set_regkey('ProxyEnable', 0)
    refersh_settings()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        set_proxy(sys.argv[1])
    else:
        unset_proxy()
