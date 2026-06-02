"""
端到端（E2E）测试套件

使用 Playwright 进行浏览器自动化测试

安装依赖：
pip install playwright pytest-playwright
playwright install

运行测试：
pytest tests/e2e/ -v
"""

import pytest
from playwright.sync_api import Page, expect


class TestLoginFlow:
    """登录流程测试"""

    def test_login_success(self, page: Page):
        """测试：成功登录"""
        # 访问登录页面
        page.goto("http://localhost:5173/auth/login")

        # 填写登录表单
        page.fill('input[type="text"]', "admin")
        page.fill('input[type="password"]', "admin123456")

        # 点击登录按钮
        page.click('button[type="submit"]')

        # 等待跳转到工作台
        page.wait_for_url("**/dashboard")

        # 验证登录成功
        expect(page).to_have_url("http://localhost:5173/dashboard")

    def test_login_wrong_password(self, page: Page):
        """测试：错误密码登录失败"""
        page.goto("http://localhost:5173/auth/login")

        page.fill('input[type="text"]', "admin")
        page.fill('input[type="password"]', "wrong_password")

        page.click('button[type="submit"]')

        # 应该显示错误消息
        error_message = page.locator(".el-message--error")
        expect(error_message).to_be_visible()

    def test_login_empty_fields(self, page: Page):
        """测试：空字段验证"""
        page.goto("http://localhost:5173/auth/login")

        # 直接点击登录按钮
        page.click('button[type="submit"]')

        # 应该显示验证错误
        # 注意：具体的选择器需要根据实际页面调整
        validation_error = page.locator(".el-form-item__error")
        expect(validation_error).to_be_visible()


class TestDashboard:
    """工作台测试"""

    @pytest.fixture(autouse=True)
    def login(self, page: Page):
        """自动登录"""
        page.goto("http://localhost:5173/auth/login")
        page.fill('input[type="text"]', "admin")
        page.fill('input[type="password"]', "admin123456")
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard")

    def test_dashboard_loads(self, page: Page):
        """测试：工作台加载"""
        # 验证工作台页面元素
        expect(page.locator("h1")).to_contain_text("工作台")

    def test_dashboard_statistics(self, page: Page):
        """测试：统计数据显示"""
        # 验证统计卡片存在
        stat_cards = page.locator(".stat-card")
        expect(stat_cards).to_have_count(4)  # 假设有 4 个统计卡片


class TestVillageManagement:
    """帮扶村管理测试"""

    @pytest.fixture(autouse=True)
    def login(self, page: Page):
        """自动登录"""
        page.goto("http://localhost:5173/auth/login")
        page.fill('input[type="text"]', "admin")
        page.fill('input[type="password"]', "admin123456")
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard")

    def test_village_list(self, page: Page):
        """测试：帮扶村列表"""
        # 导航到帮扶村列表
        page.goto("http://localhost:5173/villages")

        # 验证列表加载
        table = page.locator(".el-table")
        expect(table).to_be_visible()

    def test_village_search(self, page: Page):
        """测试：帮扶村搜索"""
        page.goto("http://localhost:5173/villages")

        # 输入搜索关键词
        search_input = page.locator('input[placeholder*="搜索"]')
        search_input.fill("测试村")

        # 点击搜索按钮
        page.click('button:has-text("搜索")')

        # 等待搜索结果
        page.wait_for_timeout(1000)

        # 验证搜索结果
        # 注意：具体验证逻辑需要根据实际情况调整

    def test_village_create(self, page: Page):
        """测试：创建帮扶村"""
        page.goto("http://localhost:5173/villages")

        # 点击新建按钮
        page.click('button:has-text("新建")')

        # 填写表单
        page.fill('input[placeholder*="村名"]', "测试村庄")
        page.fill('input[placeholder*="编码"]', "TEST001")

        # 提交表单
        page.click('button:has-text("确定")')

        # 验证成功消息
        success_message = page.locator(".el-message--success")
        expect(success_message).to_be_visible()


class TestProjectManagement:
    """项目管理测试"""

    @pytest.fixture(autouse=True)
    def login(self, page: Page):
        """自动登录"""
        page.goto("http://localhost:5173/auth/login")
        page.fill('input[type="text"]', "admin")
        page.fill('input[type="password"]', "admin123456")
        page.click('button[type="submit"]')
        page.wait_for_url("**/dashboard")

    def test_project_list(self, page: Page):
        """测试：项目列表"""
        page.goto("http://localhost:5173/projects")

        # 验证列表加载
        table = page.locator(".el-table")
        expect(table).to_be_visible()

    def test_project_filter(self, page: Page):
        """测试：项目筛选"""
        page.goto("http://localhost:5173/projects")

        # 选择项目状态筛选
        page.click('.el-select:has-text("状态")')
        page.click('.el-select-dropdown__item:has-text("进行中")')

        # 等待筛选结果
        page.wait_for_timeout(1000)

        # 验证筛选结果
        # 注意：具体验证逻辑需要根据实际情况调整


class TestResponsiveDesign:
    """响应式设计测试"""

    @pytest.mark.parametrize("viewport", [
        {"width": 1920, "height": 1080},  # Full HD
        {"width": 1366, "height": 768},   # HD
        {"width": 1280, "height": 1024},  # SXGA
        {"width": 1024, "height": 768},   # XGA
    ])
    def test_responsive_layout(self, page: Page, viewport):
        """测试：不同分辨率下的布局"""
        # 设置视口大小
        page.set_viewport_size(viewport)

        # 访问登录页面
        page.goto("http://localhost:5173/auth/login")

        # 验证页面可见
        login_form = page.locator("form")
        expect(login_form).to_be_visible()

        # 验证关键元素可见
        username_input = page.locator('input[type="text"]')
        password_input = page.locator('input[type="password"]')
        submit_button = page.locator('button[type="submit"]')

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(submit_button).to_be_visible()


class TestAccessibility:
    """可访问性测试"""

    def test_keyboard_navigation(self, page: Page):
        """测试：键盘导航"""
        page.goto("http://localhost:5173/auth/login")

        # 使用 Tab 键导航
        page.keyboard.press("Tab")  # 聚焦到用户名输入框
        page.keyboard.type("admin")

        page.keyboard.press("Tab")  # 聚焦到密码输入框
        page.keyboard.type("admin123456")

        page.keyboard.press("Tab")  # 聚焦到登录按钮
        page.keyboard.press("Enter")  # 按 Enter 提交

        # 验证登录成功
        page.wait_for_url("**/dashboard")
        expect(page).to_have_url("http://localhost:5173/dashboard")

    def test_focus_indicators(self, page: Page):
        """测试：焦点指示器"""
        page.goto("http://localhost:5173/auth/login")

        # 聚焦到输入框
        username_input = page.locator('input[type="text"]')
        username_input.focus()

        # 验证焦点样式
        # 注意：具体的验证方式需要根据实际 CSS 调整
        focused_element = page.evaluate("document.activeElement.tagName")
        assert focused_element == "INPUT"


# Playwright 配置
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """浏览器上下文配置"""
    return {
        **browser_context_args,
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "locale": "zh-CN",
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """浏览器启动参数"""
    return {
        **browser_type_launch_args,
        "headless": True,  # 无头模式，设置为 False 可以看到浏览器
        "slow_mo": 100,    # 减慢操作速度，便于观察
    }
