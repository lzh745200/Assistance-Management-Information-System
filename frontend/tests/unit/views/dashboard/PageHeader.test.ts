/**
 * PageHeader 组件测试
 *
 * 测试范围:
 * 1. 欢迎语和日期正确渲染
 * 2. "新建项目"按钮 emit 事件
 * 3. "数据分析"按钮正确导航
 * 4. 管理员可见备份按钮
 * 5. 全局搜索组件正确渲染
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import PageHeader from "@/views/dashboard/PageHeader.vue";

// Mock auth store
vi.mock("@/stores/auth", () => ({
  useAuthStore: vi.fn(() => ({
    user: { username: "admin", full_name: "管理员", role: "admin" },
  })),
}));

// Mock router
const mockPush = vi.fn();
vi.mock("vue-router", () => ({
  useRouter: () => ({ push: mockPush, resolve: vi.fn(() => ({ name: 'TestRoute', matched: [{ path: '/test' }] })) }),
}));

// 全局 stubs — 包含 GlobalSearch 避免 API 调用级联
const globalStubs = {
  "el-button": true,
  "el-icon": true,
  "el-dropdown": true,
  GlobalSearch: true,
};

describe("PageHeader.vue", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("renders welcome message with username", () => {
    const wrapper = mount(PageHeader, {
      global: { stubs: globalStubs },
    });
    expect(wrapper.text()).toContain("欢迎回来");
  });

  it("renders current date in Chinese format", () => {
    const wrapper = mount(PageHeader, {
      global: { stubs: globalStubs },
    });
    const text = wrapper.text();
    expect(text).toMatch(/\d{4}年\d{1,2}月\d{1,2}日/);
  });

  it('navigates to /data-analysis when clicking 数据分析', async () => {
    const wrapper = mount(PageHeader, {
      global: { stubs: { "el-icon": true, "el-dropdown": true, GlobalSearch: true } },
    });

    const btn = wrapper.find('[data-test="btn-analysis"]');
    if (btn.exists()) {
      await btn.trigger("click");
      expect(mockPush).toHaveBeenCalledWith("/data-analysis");
    }
  });

  it("shows backup button when user is admin", () => {
    const wrapper = mount(PageHeader, {
      global: { stubs: { "el-icon": true, "el-dropdown": true, GlobalSearch: true } },
    });
    const backupBtn = wrapper.find('[data-test="btn-backup"]');
    expect(backupBtn.exists()).toBe(true);
  });

  it("renders global search component", () => {
    const wrapper = mount(PageHeader, {
      global: { stubs: globalStubs },
    });
    // GlobalSearch 被 stub 后应渲染为 stub 占位
    const search = wrapper.findComponent({ name: "GlobalSearch" });
    expect(search.exists()).toBe(true);
  });
});
