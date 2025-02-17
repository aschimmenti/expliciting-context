<!-- App.vue -->
<template>
  <div class="min-h-screen bg-gray-100">
    <JsonEventEvaluator />
  </div>
</template>

<script>
import JsonEventEvaluator from './components/JsonEvaluator.vue'

export default {
  name: 'App',
  components: {
    JsonEventEvaluator
  }
}
</script>