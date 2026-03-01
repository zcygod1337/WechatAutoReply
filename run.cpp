// code:gbk
#include<iostream>
#include<windows.h>
using namespace std;
const wchar_t* SUB_KEY = L"Software\\Microsoft\\Narrator\\NoRoam";
const wchar_t* VALUE_NAME = L"RunningState";
bool SetNarratorRunningStateToTrue() {
    /*
    Function: SetNarratorRunningStateToTrue
    Description: 将注册表项 HKEY_CURRENT_USER\Software\Microsoft\Narrator\NoRoam\RunningState 设置为 1（真）。
    Returns: true 如果成功设置 RunningState 为 1，否则返回 false。
    dev by AI
    */
    HKEY hKey = nullptr;
    DWORD dwDisposition = 0;         
    DWORD value = 0;
    DWORD dataSize = sizeof(value);
    DWORD dataType = 0;
    LONG result;
    result = RegCreateKeyExW(
        HKEY_CURRENT_USER,
        SUB_KEY,
        0,
        nullptr,
        REG_OPTION_NON_VOLATILE,
        KEY_QUERY_VALUE | KEY_SET_VALUE, 
        nullptr,
        &hKey,
        &dwDisposition
    );

    if (result != ERROR_SUCCESS) {
        std::cerr << "无法打开或创建注册表键，错误代码: " << result << std::endl;
        return false;
    }
    result = RegQueryValueExW(
        hKey,
        VALUE_NAME,
        nullptr,
        &dataType,
        reinterpret_cast<LPBYTE>(&value),
        &dataSize
    );

    if (result == ERROR_SUCCESS) {
        if (dataType != REG_DWORD) {
            std::cerr << "RunningState 不是预期的 DWORD 类型，无法安全修改。" << std::endl;
            RegCloseKey(hKey);
            return false;
        }
        if (value == 1) {
            std::cout << "RunningState 已经是 1（真），无需修改。" << std::endl;
            RegCloseKey(hKey);
            return true;
        }
    }
    else if (result == ERROR_FILE_NOT_FOUND) {
        std::cout << "RunningState 不存在，将创建并设置为 1。" << std::endl;
    }
    else {
        std::cerr << "查询注册表值失败，错误代码: " << result << std::endl;
        RegCloseKey(hKey);
        return false;
    }
    value = 1;
    result = RegSetValueExW(
        hKey,
        VALUE_NAME,
        0,
        REG_DWORD,
        reinterpret_cast<const BYTE*>(&value),
        sizeof(value)
    );
    if (result != ERROR_SUCCESS) {
        std::cerr << "设置注册表值失败，错误代码: " << result << std::endl;
        RegCloseKey(hKey);
        return false;
    }
    std::cout << "成功将 RunningState 设置为 1（真）。" << std::endl;
    RegCloseKey(hKey);
    return true;
}
bool IsRunningAsAdmin() {
    /*
        Function: IsRunningAsAdmin
        Description: 检查当前程序是否以管理员权限运行。
        Returns: true 如果程序以管理员权限运行，否则返回 false。\
        dev by AI
    */
    BOOL isAdmin = FALSE;
    PSID adminGroupSid = nullptr;
    SID_IDENTIFIER_AUTHORITY ntAuthority = SECURITY_NT_AUTHORITY;
    if (!AllocateAndInitializeSid(&ntAuthority,2,                           
            SECURITY_BUILTIN_DOMAIN_RID, 
            DOMAIN_ALIAS_RID_ADMINS,    
            0, 0, 0, 0, 0, 0,
            &adminGroupSid)) {
        return false;
    }
    if (!CheckTokenMembership(nullptr, adminGroupSid, &isAdmin)) {
        isAdmin = FALSE; 
    }
    FreeSid(adminGroupSid);
    return (isAdmin == TRUE);
}
int main()
{
    if (!IsRunningAsAdmin()) {
        cout << "请以管理员权限运行此程序。" << endl;
        system("pause");
        return 0;
    }
    cout <<"本项目基于MIT协议开源，使用本程序即表示同意MIT协议的相关条款。" << endl;
    cout <<"本项目的源代码托管在GitHub上，使用本程序产生的一切后果由使用者自行承担。" << endl;
    cout <<"如果您同意上述条款，请按任意键继续..." << endl;
    while(true)
    {
        if(GetAsyncKeyState(VK_RETURN))
        {
            break;
        }
    }
    if (SetNarratorRunningStateToTrue()) {
        cout << "操作完成" << endl;
    } else {
        cout << "操作失败，按任意键退出..." << endl;
        return 0;
    }
    system("taskkill /IM Weixin.exe /f /t");
    cout << "请重新打开微信！" << endl;
    system("pause");
    cout << "环境配置完成，正在启动程序..." << endl;
    cout << "注意：请点击要回复窗口的输入框"<<endl;
    system("pause");
    system(".\\python\\python.exe .\\main.py");
    return 0;
}