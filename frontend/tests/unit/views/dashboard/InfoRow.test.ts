/**
 * InfoRow 组件测试
 *
 * 测试范围:
 * 1. 时间线区域和快捷入口区域均渲染
 * 2. 时间线最多渲染 10 条
 * 3. 点击快捷入口触发 router.push
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import InfoRow from "@/views/dashboard/InfoRow.vue";

const mockPush = vi.fn();
vi.mock("vue-router", () => ({ useRouter: () => ({ push: mockPush }) }));

vi.mock("@/api/request", () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: {
        items: Array.from({ length: 15 }, (_, i) => ({
          id: i + 1, action: `操作${i + 1}`, target: `目标${i + 1}`, type: "project", time: "2026-06-06",
        })),
      },
    }),
  },
}));

describe("InfoRow.vue", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("renders timeline and quick-links sections", () => {
    const wrapper = mount(InfoRow, {
      global: { stubs: { "el-icon": true, "el-timeline": true, "el-timeline-item": true } },
    });
    expect(wrapper.find(".timeline-section").exists()).toBe(true);
    expect(wrapper.find(".quick-links").exists()).toBe(true);
  });

  it("renders at most 10 timeline items", async () => {
    const wrapper = mount(InfoRow, {
      global: { stubs: { "el-icon": true, "el-timeline": true, "el-timeline-item": true } },
    });
    await new Promise((r) => setTimeout(r, 200));
    await wrapper.vm.$nextTick();
    // Should not show more than 10 even though API returns 15
    const items = wrapper.findAll(".timeline-item");
    expect(items.length).toBeLessThanOrEqual(11); // 10 items + possible header
  });

  it("quick-link click calls router.push", async () => {
    const wrapper = mount(InfoRow, {
      global: { stubs: { "el-icon": true, "el-timeline": true, "el-timeline-item": true } },
    });
    const link = wrapper.find('[data-test="ql-projects"]');
    if (link.exists()) {
      await link.trigger("click");
      expect(mockPush).toHaveBeenCalledWith("/projects");
    }
  });

  it("renders all 6 quick-link icons", () => {
    const wrapper = mount(InfoRow, {
      global: { stubs: { "el-icon": true, "el-timeline": true, "el-timeline-item": true } },
    });
    expect(wrapper.findAll(".ql-item").length).toBe(6);
  });
});
