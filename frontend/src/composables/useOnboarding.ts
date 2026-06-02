/**
 * 新手引导 Composable
 *
 * 使用 driver.js 在用户首次访问系统时展示功能引导。
 * 引导完成/跳过后在 localStorage 标记，不再重复展示。
 */
import { onMounted } from "vue";
import { driver, type DriveStep } from "driver.js";
import "driver.js/dist/driver.css";

const STORAGE_KEY = "onboarding_completed";
const ONBOARDING_VERSION = 2; // 更新此版本号可重新触发引导

/** Dashboard 页面引导步骤 */
const dashboardSteps: DriveStep[] = [
  {
    element: ".sidebar .nav-item:first-child",
    popover: {
      title: "工作台",
      description: "这是您的首页，展示系统核心数据和待办事项。",
      side: "right",
      align: "start",
    },
  },
  {
    element: ".sidebar .nav-item:nth-child(2)",
    popover: {
      title: "帮扶村管理",
      description: "管理帮扶村基础信息、年度数据和人口变化情况。",
      side: "right",
      align: "start",
    },
  },
  {
    element: ".sidebar .nav-item:nth-child(3)",
    popover: {
      title: "帮扶学校管理",
      description: "管理帮扶学校基本信息、助学兴教项目及资助学生情况。",
      side: "right",
      align: "start",
    },
  },
  {
    element: ".sidebar .nav-item:nth-child(4)",
    popover: {
      title: "帮扶项目管理",
      description: "在这里管理所有乡村振兴帮扶项目，支持创建、编辑和审批。",
      side: "right",
      align: "start",
    },
  },
  {
    element: ".sidebar .nav-item:nth-child(5)",
    popover: {
      title: "经费管理",
      description: "跟踪帮扶经费的拨付、使用和审计情况。",
      side: "right",
      align: "start",
    },
  },
  {
    element: ".header-right",
    popover: {
      title: "个人设置",
      description: "点击头像可修改个人资料和密码，或退出系统。",
      side: "bottom",
      align: "end",
    },
  },
  {
    popover: {
      title: "快捷键提示",
      description:
        "按 Ctrl+/ 可随时查看键盘快捷键帮助，按 G→D 快速跳转工作台。",
    },
  },
];

/**
 * 初始化新手引导
 * @param options.force 是否强制显示（忽略已完成标记）
 */
export function useOnboarding(options?: { force?: boolean }) {
  const startTour = () => {
    const driverObj = driver({
      showProgress: true,
      showButtons: ["next", "previous", "close"],
      nextBtnText: "下一步",
      prevBtnText: "上一步",
      doneBtnText: "完成",
      progressText: "{{current}} / {{total}}",
      steps: dashboardSteps,
      onDestroyed: () => {
        // 引导完成或跳过后标记
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({
            version: ONBOARDING_VERSION,
            completedAt: Date.now(),
          }),
        );
      },
    });
    driverObj.drive();
  };

  const shouldShow = (): boolean => {
    if (options?.force) return true;
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return true;
      const data = JSON.parse(stored);
      // 版本升级后重新引导
      return data.version !== ONBOARDING_VERSION;
    } catch {
      return true;
    }
  };

  onMounted(() => {
    if (shouldShow()) {
      // 延迟启动，等页面渲染完成
      setTimeout(startTour, 800);
    }
  });

  return { startTour };
}
