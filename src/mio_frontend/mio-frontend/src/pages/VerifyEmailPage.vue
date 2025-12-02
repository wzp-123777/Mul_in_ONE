<template>
  <q-layout view="lHh Lpr lFf">
    <q-page-container>
      <q-page class="flex flex-center bg-gradient">
        <div class="q-pa-md" style="max-width: 450px; width: 100%">
          <q-card>
            <q-card-section class="text-center q-pb-none">
              <div class="text-h4 text-weight-bold q-mb-sm">
                <q-icon :name="status === 'success' ? 'check_circle' : status === 'error' ? 'error' : 'hourglass_empty'" 
                        :color="status === 'success' ? 'positive' : status === 'error' ? 'negative' : 'grey'" 
                        size="xl" />
              </div>
              <div class="text-h5 q-mb-sm">{{ title }}</div>
              <div class="text-subtitle2 text-grey-7">{{ message }}</div>
            </q-card-section>

            <q-card-section class="text-center">
              <q-btn
                v-if="status === 'success'"
                label="立即登录"
                color="primary"
                @click="router.push('/login')"
                class="q-mt-md"
              />
              <q-btn
                v-else-if="status === 'error'"
                label="返回首页"
                color="primary"
                outline
                @click="router.push('/')"
                class="q-mt-md"
              />
              <q-spinner v-else color="primary" size="50px" class="q-mt-md" />
            </q-card-section>
          </q-card>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { api } from '../api'

const router = useRouter()
const route = useRoute()

const status = ref<'loading' | 'success' | 'error'>('loading')
const title = ref('验证中...')
const message = ref('请稍候，正在验证你的邮箱')

onMounted(async () => {
  const token = route.query.token as string
  
  if (!token) {
    status.value = 'error'
    title.value = '验证失败'
    message.value = '缺少验证令牌'
    return
  }
  
  try {
    await api.post('/auth/verify', { token })
    status.value = 'success'
    title.value = '验证成功！'
    message.value = '你的邮箱已验证，现在可以登录使用了'
  } catch (error: any) {
    status.value = 'error'
    title.value = '验证失败'
    message.value = error.response?.data?.detail || '验证令牌无效或已过期'
  }
})
</script>

<style scoped>
.bg-gradient {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
}
</style>
