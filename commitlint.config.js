module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat', 'fix', 'refactor', 'docs', 'test', 'build', 'chore', 'perf', 'ci', 'style'
    ]],
    'subject-case': [0],
  },
};
