<template>
  <div id="test-app">
    <h1>Test Page</h1>
    <p>If you see this, Vue is working</p>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";

onMounted(() => {
  console.log("App mounted successfully!");
});
</script>

<style>
#test-app {
  padding: 20px;
}
</style>
