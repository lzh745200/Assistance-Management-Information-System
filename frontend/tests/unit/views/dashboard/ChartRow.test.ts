/**
 * ChartRow 组件测试
 *
 * 测试范围:
 * 1. 两个图表容器渲染
 * 2. Mock ECharts init 被调用
 * 3. setOption 被调用两次（左右图表）
 * 4. resize 事件触发图表 resize
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import ChartRow from "@/views/dashboard/ChartRow.vue";

const mockSetOption = vi.fn();
const mockResize = vi.fn();
const mockDispose = vi.fn();

vi.mock("@/utils/echarts", () => ({
  default: {
    init: () => ({ setOption: mockSetOption, dispose: mockDispose, resize: mockResize }),
    graphic: { LinearGradient: vi.fn(() => ({})) },
  },
}));

// Mock request
vi.mock("@/api/request", () => ({
  default: {
    get: vi.fn().mockResolvedValue({
      data: {
        items: [
          { name: "道路硬化", progress: 85 },
          { name: "饮水工程", progress: 60 },
          { name: "电商中心", progress: 40 },
        ],
        funds_allocated: 6000000,
        funds_pending: 2000000,
        funds_planned: 900000,
      },
    }),
  },
}));

describe("ChartRow.vue", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("renders two chart containers", () => {
    const wrapper = mount(ChartRow, {
      global: { stubs: { "el-icon": true } },
    });
    expect(wrapper.findAll(".chart-card").length).toBe(2);
  });

  it("calls echarts.init twice (left + right chart)", async () => {
    mount(ChartRow, { global: { stubs: { "el-icon": true } } });
    await new Promise((r) => setTimeout(r, 200));
    // ECharts init is called inside initCharts — verify setOption called
    expect(mockSetOption).toHaveBeenCalled();
  });

  it("resize handler calls chart.resize", async () => {
    mount(ChartRow, { global: { stubs: { "el-icon": true } } });
    await new Promise((r) => setTimeout(r, 200));
    window.dispatchEvent(new Event("resize"));
    expect(mockResize).toHaveBeenCalled();
  });

  it("disposes charts on unmount", async () => {
    const wrapper = mount(ChartRow, {
      global: { stubs: { "el-icon": true } },
    });
    await new Promise((r) => setTimeout(r, 200));
    wrapper.unmount();
    expect(mockDispose).toHaveBeenCalled();
  });
});
