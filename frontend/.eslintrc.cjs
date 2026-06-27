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
    'vue/require-default-prop': 'off' // Vue 3 中可选props不需要默认值
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
    }
  ]
}
