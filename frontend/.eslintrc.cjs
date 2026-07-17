module.exports = {
  root: true,
  env: {
    node: true,
    browser: true,
    es2021: true
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-recommended',
    '@vue/eslint-config-typescript',
    '@vue/eslint-config-prettier'
  ],
  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module'
  },
  plugins: ['vue'],
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'vue/multi-word-component-names': 'off',
    'vue/require-default-prop': 'off', // Vue 3 中可选props不需要默认值
    // 禁止 response.data.success 双重解包：
    // get/post/apiRequest 返回已解包的 envelope body，success 在顶层。
    // 访问 response.data.success 会得到 undefined，导致 if 判断恒假、功能静默失效。
    'no-restricted-syntax': [
      'error',
      {
        selector: "MemberExpression[object.property.name='data'][property.name='success']",
        message: "禁止 response.data.success 双重解包。get/post/apiRequest 返回已解包的 envelope，请直接用 response.success。详见 AGENTS.md Bug 模式 #1。"
      }
    ]
  },
  overrides: [
    {
      // 帮助中心需要渲染后端受信任的 HTML 文档内容，v-html 为有意使用：
      //  - 文章正文：来自系统帮助文档库（受信任）
      //  - 搜索摘要高亮：highlightKeyword 已对用户输入做正则转义
      files: ['src/views/help/HelpCenter.vue'],
      rules: {
        'vue/no-v-html': 'off'
      }
    },
    {
      // src/types/index.ts 是纯 re-export barrel；@typescript-eslint 8.63.0 的
      // no-unused-vars 在 export * 上崩溃（Cannot use 'in' operator ... undefined）。
      // 仅对此文件关闭，避免全局放松未使用变量检查。
      files: ['src/types/index.ts'],
      rules: {
        '@typescript-eslint/no-unused-vars': 'off'
      }
    }
  ]
}
