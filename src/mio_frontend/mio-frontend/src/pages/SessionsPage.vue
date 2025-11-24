<template>
  <q-page padding>
    <div class="row items-center justify-between q-mb-md">
      <div class="text-h4">Sessions</div>
      <q-btn color="primary" icon="add" label="New Session" @click="openCreateSessionDialog" :loading="creating" />
    </div>

    <div v-if="loading" class="flex flex-center q-pa-lg">
      <q-spinner size="3em" color="primary" />
    </div>

    <q-list v-else bordered separator class="rounded-borders">
      <q-item 
        v-for="session in sessions" 
        :key="session.id" 
        clickable 
        v-ripple 
        :to="`/chat/${session.id}`"
      >
        <q-item-section avatar>
          <q-icon name="chat_bubble" color="primary" />
        </q-item-section>
        <q-item-section>
          <q-item-label>Session #{{ session.id }}</q-item-label>
          <q-item-label caption>{{ new Date(session.created_at).toLocaleString() }}</q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-icon name="chevron_right" />
        </q-item-section>
      </q-item>
      <q-item v-if="sessions.length === 0">
        <q-item-section class="text-center text-grey">
          No sessions found. Create one to start chatting.
        </q-item-section>
      </q-item>
    </q-list>

    <!-- Create Session Dialog -->
    <q-dialog v-model="showCreateDialog">
      <q-card style="min-width: 450px">
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">
            <q-icon name="add_circle" class="q-mr-sm" />
            Create New Session
          </div>
        </q-card-section>

        <q-card-section>
          <div class="text-subtitle2 q-mb-sm">Optional: Set your roleplay persona</div>
          <q-input
            v-model="newSessionPersona"
            outlined
            autogrow
            type="textarea"
            label="Your character (optional)"
            placeholder="e.g., A fearless space explorer..."
            hint="Define who you are in this roleplay session"
            :maxlength="500"
            counter
            rows="3"
          >
            <template v-slot:prepend>
              <q-icon name="badge" />
            </template>
          </q-input>

          <div class="q-mt-md">
            <div class="text-caption text-grey-7 q-mb-sm">Quick templates:</div>
            <div class="persona-templates">
              <q-chip
                v-for="template in personaTemplates"
                :key="template.value"
                clickable
                @click="newSessionPersona = template.label"
                color="primary"
                outline
                size="sm"
              >
                {{ template.label }}
              </q-chip>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="grey" v-close-popup />
          <q-btn
            flat
            label="Create"
            color="primary"
            @click="handleCreateSession"
            :loading="creating"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getSessions, createSession, type Session, authState } from '../api'
import { useQuasar } from 'quasar'

const sessions = ref<Session[]>([])
const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)
const newSessionPersona = ref('')
const router = useRouter()
const $q = useQuasar()

const personaTemplates = [
  { value: 'hero', label: 'A fearless hero on a quest' },
  { value: 'detective', label: 'A sharp-minded detective' },
  { value: 'merchant', label: 'A cunning merchant' },
  { value: 'scholar', label: 'A wise scholar' },
  { value: 'adventurer', label: 'A curious adventurer' },
]

const loadSessions = async () => {
  loading.value = true
  try {
    sessions.value = await getSessions()
  } catch (e) {
    $q.notify({
      type: 'negative',
      message: 'Failed to load sessions'
    })
  } finally {
    loading.value = false
  }
}

const openCreateSessionDialog = () => {
  newSessionPersona.value = ''
  showCreateDialog.value = true
}

const handleCreateSession = async () => {
  creating.value = true
  try {
    const persona = newSessionPersona.value.trim() || undefined
    const newSessionId = await createSession(persona)
    showCreateDialog.value = false
    router.push(`/chat/${newSessionId}`)
  } catch (e) {
    $q.notify({
      type: 'negative',
      message: 'Failed to create session'
    })
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadSessions()
})
</script>

<style scoped>
.persona-templates {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
