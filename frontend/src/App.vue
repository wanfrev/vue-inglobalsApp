<script setup>
import { onMounted, ref } from 'vue'
import AppNav from './components/layout/AppNav.vue'
import AppHeader from './components/layout/AppHeader.vue'
import EmulatorView from './views/EmulatorView.vue'
import HistoryView from './views/HistoryView.vue'
import AuthView from './views/AuthView.vue'
import { getMe } from './services/api.js'
import { authToken, currentUser, currentView, logoutSession } from './stores/appStore.js'

const isRestoringSession = ref(!!authToken.value)

onMounted(async () => {
  if (!authToken.value) return
  try {
    const status = await getMe()
    currentUser.value = status
  } catch {
    logoutSession()
  } finally {
    isRestoringSession.value = false
  }
})
</script>

<template>
  <div class="flex h-dvh flex-col overflow-hidden bg-gradient-to-b from-slate-50 via-white to-slate-100 text-azulCorp">
    <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div class="absolute left-[12%] top-[-180px] h-[460px] w-[460px] rounded-full bg-violetaIA/10 blur-[130px]"></div>
      <div class="absolute bottom-[-220px] right-[12%] h-[520px] w-[520px] rounded-full bg-oro/10 blur-[140px]"></div>
      <div
        class="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] opacity-30 [background-size:40px_40px] [mask-image:radial-gradient(ellipse_60%_60%_at_50%_50%,#000_40%,transparent_100%)]"
      ></div>
    </div>

    <template v-if="!authToken || !currentUser">
      <AppHeader />
      <main v-if="isRestoringSession" class="flex flex-1 items-center justify-center">
        <p class="text-sm text-slate-400">Cargando...</p>
      </main>
      <AuthView v-else />
    </template>
    <template v-else>
      <AppHeader />
      <AppNav />
      <main class="mx-auto flex w-full min-h-0 max-w-[1440px] flex-1 flex-col px-4 pb-3 sm:px-6 lg:px-10">
        <EmulatorView v-if="currentView === 'emulator'" />
        <HistoryView v-else-if="currentView === 'history'" />
      </main>
      <p class="shrink-0 pb-2 text-center text-[10px] text-slate-400">
        © {{ new Date().getFullYear() }} Inglobals. Todos los derechos reservados.
      </p>
    </template>
  </div>
</template>
