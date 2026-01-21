<template>
  <div class="app-shell">
    <SessionPanel />
    <DocumentsPanel />
    <ChatPanel />
    <FlashcardPanel />
  </div>
</template>

<style scoped>
.app-shell {
  height: 100%;
  display: flex;
  flex-direction: row;
  min-height: 0;
  overflow: hidden;
}
</style>
