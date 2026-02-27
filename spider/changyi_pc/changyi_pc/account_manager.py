import json
import os


class AccountManager:
    def __init__(self, json_file='accounts.json', index_file='account_index.json'):
        self.json_file = json_file
        self.index_file = index_file
        self.accounts = self._load_accounts()
        self.current_index = self._load_index()

    def _load_accounts(self):
        """加载 JSON 文件中的账号数据"""
        if not os.path.exists(self.json_file):
            return []
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("JSON 文件格式错误，返回空列表")
            return []

    def _save_accounts(self):
        """将账号数据保存回 JSON 文件"""
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(self.accounts, f, ensure_ascii=False, indent=4)

    def _load_index(self):
        """加载当前轮巡索引"""
        if not os.path.exists(self.index_file):
            return 0
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('index', 0)
        except:
            return 0

    def _save_index(self):
        """保存当前轮巡索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump({'index': self.current_index}, f, ensure_ascii=False, indent=4)

    def get_account(self, account_name):
        """根据账号名获取账号信息"""
        for account in self.accounts:
            if account_name in account:
                return account[account_name]
        return None

    def get_next_account(self, save_index=True):
        """
        轮巡获取下一个账号信息
        :param save_index: 是否保存索引到文件（默认保存）
        :return: (账号名，账号信息) 或 (None, None)
        """
        if not self.accounts:
            return None, None

        # 获取当前索引对应的账号
        current_account = self.accounts[self.current_index]
        account_name = list(current_account.keys())[0]
        account_info = current_account[account_name]
        # 更新索引（循环）
        self.current_index = (self.current_index + 1) % len(self.accounts)

        # 保存索引
        if save_index:
            self._save_index()

        return account_name, account_info

    def get_all_accounts(self):
        """获取所有账号名列表"""
        return [list(account.keys())[0] for account in self.accounts]

    def get_account_count(self):
        """获取账号总数"""
        return len(self.accounts)

    def reset_index(self):
        """重置轮巡索引到第一个账号"""
        self.current_index = 0
        self._save_index()

    def update_cookies(self, account_name, new_cookies):
        """更新指定账号的 cookies 数据"""
        for account in self.accounts:
            if account_name in account:
                account[account_name]['cookies'] = new_cookies
                self._save_accounts()
                return True
        return False


# 示例用法
if __name__ == '__main__':
    manager = AccountManager('accounts.json')

    print(f"总账号数：{manager.get_account_count()}")
    print(f"所有账号：{manager.get_all_accounts()}")
    print("-" * 50)

    # 轮巡获取账号（示例：循环 5 次）
    print("轮巡获取账号信息：")
    for i in range(5):
        account_name, account_info = manager.get_next_account()
        if account_name:
            print(f"第 {i + 1} 次：账号名 = {account_name}, loginid = {account_info.get('loginid')}")
        else:
            print(f"第 {i + 1} 次：无可用账号")

    print("-" * 50)

    # 查询特定账号
    account_info = manager.get_account('19876775931')
    if account_info:
        print("指定账号信息：", account_info)
    else:
        print("未找到指定账号")

    # 更新 cookies
    # new_cookies = {'session': 'xyz123', 'token': 'abc456'}
    # if manager.update_cookies('19876775931', new_cookies):
    #     print("账号 cookies 已更新")
    # else:
    #     print("更新失败")

    # 重置索引
    # manager.reset_index()
    # print("轮巡索引已重置")