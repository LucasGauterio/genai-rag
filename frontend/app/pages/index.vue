<template>
  <div class="app-shell">
    <DocumentsPanel />
    <ChatPanel />
  </div>
</template>

<style scoped>
/*
  CRITICAL: Full-height app shell layout
  
  This is the core layout structure that makes the app behave like NotebookLM:
  - The app-shell fills 100% of the parent height (which is 100vh via CSS chain)
  - It uses flex to create two side-by-side panels
  - Each panel stretches from top to bottom
  - Only inner areas (document list, messages) scroll
  - The chat input stays fixed at the bottom
*/

.app-shell {
  height: 100%;
  display: flex;
  flex-direction: row;
  /* CRITICAL: min-height: 0 breaks the default min-height: auto behavior of flex items,
     which is required for nested flex children to be able to scroll */
  min-height: 0;
  overflow: hidden;
}
</style>
