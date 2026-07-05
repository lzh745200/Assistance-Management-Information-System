/**
 * GlobalSearch 组件测试
 *
 * 测试范围:
 * 1. 搜索框正确渲染
 * 2. 防抖后触发 API 调用
 * 3. 空结果状态显示
 * 4. 点击结果项导航
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { defineComponent } from "vue";
import GlobalSearch from "@/views/dashboard/components/GlobalSearch.vue";

// Mock search API
const mockGlobalSearch = vi.fn();
vi.mock("@/api/search", () => ({
  globalSearch: (...args: any[]) => mockGlobalSearch(...args),
  SEARCH_TYPE_LABELS: {
    village: "帮扶村",
    project: "项目",
    policy: "政策法规",
    school: "学校",
    user: "用户",
  },
}));

// Mock router safe
const mockPushSafe = vi.fn();
vi.mock("@/composables/useRouterSafe", () => ({
  useRouterSafe: () => ({ pushSafe: mockPushSafe }),
}));

// Mock vue-router
vi.mock("vue-router", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

// 创建可交互的 el-input stub（渲染真实 input 元素）
const ElInputStub = defineComponent({
  name: "ElInput",
  props: ["modelValue", "placeholder", "prefixIcon", "clearable"],
  emits: ["update:modelValue", "input", "focus", "blur"],
  template: `<input
    :value="modelValue"
    :placeholder="placeholder"
    @input="$emit('update:modelValue', $event.target.value); $emit('input', $event.target.value)"
    @focus="$emit('focus')"
    @blur="$emit('blur')"
  />`,
});

const ElIconStub = { name: "ElIcon", template: "<span><slot /></span>" };
const ElTagStub = { name: "ElTag", template: "<span><slot /></span>" };
const TransitionStub = { name: "Transition", template: "<div><slot /></div>" };

const mockResults = {
  total: 3,
  items: [
    { id: 1, type: "village" as const, title: "测试村", subtitle: "贵州毕节", link: "/villages/1" },
    { id: 1, type: "project" as const, title: "扶贫项目", subtitle: "项目编号: P001", link: "/projects/1" },
    { id: 1, type: "school" as const, title: "希望小学", subtitle: "贵州省", link: "/schools/1" },
  ],
};

function mountSearch() {
  return mount(GlobalSearch, {
    global: {
      stubs: {
        "el-input": ElInputStub,
        "el-icon": ElIconStub,
        "el-tag": ElTagStub,
        transition: TransitionStub,
        Transition: TransitionStub,
      },
    },
  });
}

describe("GlobalSearch.vue", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders search input with placeholder", () => {
    const wrapper = mountSearch();
    expect(wrapper.find(".global-search").exists()).toBe(true);
    const input = wrapper.find("input");
    expect(input.exists()).toBe(true);
    expect(input.attributes("placeholder")).toContain("搜索");
  });

  it("does not search when input is empty", () => {
    const wrapper = mountSearch();
    const input = wrapper.find("input");
    input.element.value = "";
    input.trigger("input");
    vi.advanceTimersByTime(500);
    expect(mockGlobalSearch).not.toHaveBeenCalled();
  });

  it("triggers search after debounce delay", async () => {
    mockGlobalSearch.mockResolvedValue(mockResults);
    const wrapper = mountSearch();
    const input = wrapper.find("input");
    await input.setValue("测试");
    vi.advanceTimersByTime(400);
    await flushPromises();
    expect(mockGlobalSearch).toHaveBeenCalledWith("测试", 20);
  });

  it("shows no result message when search returns empty", async () => {
    mockGlobalSearch.mockResolvedValue({ total: 0, items: [] });
    const wrapper = mountSearch();
    const input = wrapper.find("input");
    await input.setValue("不存在的关键词");
    vi.advanceTimersByTime(400);
    await flushPromises();
    expect(wrapper.text()).toContain("未找到");
  });

  it("renders grouped results after search", async () => {
    mockGlobalSearch.mockResolvedValue(mockResults);
    const wrapper = mountSearch();
    const input = wrapper.find("input");
    await input.setValue("测试");
    vi.advanceTimersByTime(400);
    await flushPromises();
    // 验证分组标签存在
    expect(wrapper.text()).toContain("帮扶村");
    expect(wrapper.text()).toContain("项目");
    expect(wrapper.text()).toContain("学校");
    expect(wrapper.text()).toContain("共 3 条结果");
  });

  it("navigates when clicking a result item", async () => {
    mockGlobalSearch.mockResolvedValue(mockResults);
    const wrapper = mountSearch();
    const input = wrapper.find("input");
    await input.setValue("测试");
    vi.advanceTimersByTime(400);
    await flushPromises();
    // 点击第一个结果项
    const items = wrapper.findAll(".result-item");
    expect(items.length).toBeGreaterThan(0);
    await items[0].trigger("mousedown");
    expect(mockPushSafe).toHaveBeenCalledWith("/villages/1");
  });
});
