/**
 * 单机版测试工具
 * 用于验证系统在离线环境下的功能
 */
export async function runStandaloneTests() {
  const results: { name: string; passed: boolean; error?: string }[] = [];

  // Test API connectivity
  try {
    const response = await fetch("/api/v1/health");
    results.push({ name: "API连接", passed: response.ok });
  } catch (e: any) {
    results.push({ name: "API连接", passed: false, error: e.message });
  }

  // Test localStorage
  try {
    localStorage.setItem("_test_", "1");
    localStorage.removeItem("_test_");
    results.push({ name: "本地存储", passed: true });
  } catch (e: any) {
    results.push({ name: "本地存储", passed: false, error: e.message });
  }

  return results;
}
