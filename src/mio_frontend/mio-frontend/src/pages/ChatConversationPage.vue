<template>
  <div class="chat-conversation-page">
    <!-- Header with active agents -->
    <div class="chat-header">
      <div class="header-left">
        <q-btn flat round icon="arrow_back" @click="goBack" />
        <div class="header-title">
          <div class="title-text">Chat Session</div>
          <div v-if="selectedPersonas.length > 0" class="active-agents">
            <q-icon name="people" size="xs" />
            <span>{{ selectedPersonas.length }} agent(s) active</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <q-btn
          flat
          dense
          icon="badge"
          @click="openUserPersonaDialog"
          class="q-mr-md"
        >
          <q-tooltip>Edit your roleplay persona</q-tooltip>
          <q-badge v-if="userPersona" color="positive" floating>✓</q-badge>
        </q-btn>
        <q-select
          v-model="selectedPersonas"
          :options="personaOptions"
          multiple
          outlined
          dense
          label="Target Agents"
          option-value="value"
          option-label="label"
          emit-value
          map-options
          style="min-width: 250px"
        />
      </div>
    </div>

    <!-- Messages Area -->
    <q-scroll-area ref="scrollArea" class="messages-container">
      <!-- Loading State -->
      <div v-if="loading" class="loading-container">
        <q-spinner color="primary" size="50px" />
        <p>Loading conversation...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="messages.length === 0" class="empty-state">
        <q-icon name="chat" size="80px" color="grey-5" />
        <h5>Start a Conversation</h5>
        <p>Select agents and send a message to begin</p>
        <div class="quick-prompts">
          <q-btn
            v-for="prompt in quickPrompts"
            :key="prompt.value"
            outline
            color="primary"
            :label="prompt.label"
            @click="handlePromptClick(prompt)"
            class="q-ma-xs"
          />
        </div>
      </div>

      <!-- Messages List -->
      <div v-else class="messages-list">
        <div
          v-for="(msg, idx) in messages"
          :key="msg.id || idx"
          class="message-row"
          :class="msg.sender === 'user' ? 'message-user' : 'message-agent'"
        >
          <!-- Agent Avatar -->
          <q-avatar
            v-if="msg.sender !== 'user'"
            :color="getAgentColor(msg.sender)"
            text-color="white"
            size="40px"
            class="message-avatar"
          >
            {{ getAgentInitial(msg.sender) }}
          </q-avatar>

          <!-- Message Content -->
          <div class="message-content-wrapper">
            <div class="message-header" v-if="msg.sender !== 'user'">
              <span class="agent-name" @click="showPersonaDetails(msg.sender)">
                {{ msg.sender || 'Agent' }}
              </span>
              <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
            </div>
            <div
              class="message-bubble"
              :class="{ 'bubble-user': msg.sender === 'user', 'bubble-agent': msg.sender !== 'user' }"
            >
              <div v-if="msg.loading" class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
              <div v-else class="message-text">{{ msg.content }}</div>
            </div>
            <div class="message-actions" v-if="!msg.loading">
              <q-btn
                flat
                dense
                round
                size="sm"
                icon="content_copy"
                @click="copyMessage(msg.content)"
              >
                <q-tooltip>Copy</q-tooltip>
              </q-btn>
              <q-btn
                v-if="msg.sender !== 'user'"
                flat
                dense
                round
                size="sm"
                icon="thumb_up"
                :color="msg.feedback === 'positive' ? 'positive' : ''"
                @click="feedbackMessage(msg.id, 'positive')"
              >
                <q-tooltip>Good response</q-tooltip>
              </q-btn>
              <q-btn
                v-if="msg.sender !== 'user'"
                flat
                dense
                round
                size="sm"
                icon="thumb_down"
                :color="msg.feedback === 'negative' ? 'negative' : ''"
                @click="feedbackMessage(msg.id, 'negative')"
              >
                <q-tooltip>Poor response</q-tooltip>
              </q-btn>
              <q-btn
                v-if="msg.sender !== 'user'"
                flat
                dense
                round
                size="sm"
                icon="info"
                @click="showPersonaDetails(msg.sender)"
              >
                <q-tooltip>Agent info</q-tooltip>
              </q-btn>
            </div>
          </div>

          <!-- User Avatar -->
          <q-avatar
            v-if="msg.sender === 'user'"
            color="primary"
            text-color="white"
            size="40px"
            class="message-avatar"
          >
            <q-icon name="person" />
          </q-avatar>
        </div>
      </div>

      <!-- Quick Prompts (shown when messages exist) -->
      <div v-if="messages.length > 0" class="quick-actions">
        <q-btn
          v-for="prompt in simplePrompts"
          :key="prompt.value"
          flat
          dense
          :label="prompt.label"
          @click="handlePromptClick(prompt)"
          class="q-mr-sm"
        />
      </div>
    </q-scroll-area>

    <!-- Input Area -->
    <div class="input-container">
      <!-- Attached Files Display -->
      <div v-if="attachedFiles.length > 0" class="attached-files">
        <q-chip
          v-for="(file, idx) in attachedFiles"
          :key="idx"
          removable
          @remove="removeAttachment(idx)"
          color="primary"
          text-color="white"
          icon="attach_file"
        >
          {{ file.name }}
        </q-chip>
      </div>

      <!-- Input Row -->
      <div class="input-row">
        <!-- Action Buttons -->
        <div class="input-actions">
          <q-btn flat dense round icon="alternate_email" @click="openAgentMention" size="sm">
            <q-tooltip>Mention agent</q-tooltip>
          </q-btn>
          <q-btn flat dense round icon="description" @click="openTemplates" size="sm">
            <q-tooltip>Templates</q-tooltip>
          </q-btn>
          <q-btn flat dense round icon="attach_file" @click="openAttachment" size="sm">
            <q-tooltip>Attach file</q-tooltip>
          </q-btn>
        </div>

        <!-- Text Input -->
        <q-input
          v-model="inputValue"
          ref="inputRef"
          outlined
          dense
          placeholder="Type your message... (use @ to mention agents)"
          autogrow
          :maxlength="2000"
          @keydown.enter.exact.prevent="handleSubmit"
          @keydown="handleKeyDown"
          class="message-input"
        >
          <template v-slot:append>
            <q-btn
              round
              dense
              flat
              icon="send"
              @click="handleSubmit"
              :disable="!inputValue.trim()"
              color="primary"
            />
          </template>
        </q-input>

        <!-- Character Counter -->
        <div class="char-counter">{{ inputValue.length }}/2000</div>
      </div>
    </div>

    <!-- Agent Mention Dialog -->
    <q-dialog v-model="showAgentDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">Mention Agent</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-input
            v-model="agentSearchQuery"
            outlined
            dense
            placeholder="Search agents..."
            autofocus
          />
          <q-list class="q-mt-md">
            <q-item
              v-for="persona in filteredPersonas"
              :key="persona.id"
              clickable
              @click="mentionAgent(persona)"
              class="agent-list-item"
            >
              <q-item-section avatar>
                <q-avatar :color="getAgentColor(persona.handle)" text-color="white">
                  {{ persona.name.charAt(0) }}
                </q-avatar>
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ persona.name }}</q-item-label>
                <q-item-label caption>@{{ persona.handle }} · {{ persona.tone }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Templates Dialog -->
    <q-dialog v-model="showTemplatesDialog">
      <q-card style="min-width: 450px">
        <q-card-section>
          <div class="text-h6">Message Templates</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-list>
            <q-item
              v-for="(template, idx) in messageTemplates"
              :key="idx"
              clickable
              @click="applyTemplate(template.content)"
              class="template-item"
            >
              <q-item-section>
                <q-item-label class="text-weight-medium">{{ template.title }}</q-item-label>
                <q-item-label caption class="text-grey-7">{{ template.content }}</q-item-label>
              </q-item-section>
              <q-item-section side>
                <q-icon name="arrow_forward" />
              </q-item-section>
            </q-item>
          </q-list>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Attachment Dialog -->
    <q-dialog v-model="showAttachmentDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Upload Attachment</div>
        </q-card-section>
        <q-card-section class="q-pt-none">
          <q-file
            v-model="newAttachment"
            label="Choose files"
            outlined
            multiple
            max-files="5"
            counter
            accept="image/*,.pdf,.doc,.docx,.txt"
          >
            <template v-slot:prepend>
              <q-icon name="attach_file" />
            </template>
          </q-file>
          <div class="text-caption text-grey-7 q-mt-sm">
            Maximum 5 files. Supported: images, PDF, DOC, TXT
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="primary" v-close-popup />
          <q-btn
            flat
            label="Attach"
            color="primary"
            @click="attachFiles"
            :disable="!newAttachment || newAttachment.length === 0"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- Persona Details Dialog -->
    <q-dialog v-model="showPersonaDialog">
      <q-card style="min-width: 450px" v-if="selectedPersona">
        <q-card-section class="bg-gradient-primary text-white">
          <div class="row items-center">
            <q-avatar size="60px" :color="getAgentColor(selectedPersona.handle)" class="q-mr-md">
              {{ selectedPersona.name.charAt(0) }}
            </q-avatar>
            <div>
              <div class="text-h6">{{ selectedPersona.name }}</div>
              <div class="text-caption">@{{ selectedPersona.handle }}</div>
            </div>
          </div>
        </q-card-section>

        <q-card-section>
          <div class="persona-details">
            <div class="detail-row">
              <q-icon name="description" class="detail-icon" />
              <div class="detail-content">
                <div class="detail-label">Role</div>
                <div class="detail-value">{{ selectedPersona.prompt || 'No description' }}</div>
              </div>
            </div>

            <q-separator class="q-my-md" />

            <div class="detail-row">
              <q-icon name="psychology" class="detail-icon" />
              <div class="detail-content">
                <div class="detail-label">Tone</div>
                <div class="detail-value">{{ selectedPersona.tone }}</div>
              </div>
            </div>

            <div class="detail-row">
              <q-icon name="speed" class="detail-icon" />
              <div class="detail-content">
                <div class="detail-label">Proactivity</div>
                <q-linear-progress
                  :value="selectedPersona.proactivity"
                  color="primary"
                  class="q-mt-xs"
                />
                <div class="detail-value">{{ (selectedPersona.proactivity * 100).toFixed(0) }}%</div>
              </div>
            </div>

            <q-separator class="q-my-md" />

            <div class="detail-row" v-if="selectedPersona.api_model">
              <q-icon name="smart_toy" class="detail-icon" />
              <div class="detail-content">
                <div class="detail-label">Model</div>
                <div class="detail-value">{{ selectedPersona.api_model }}</div>
              </div>
            </div>

            <div class="detail-row">
              <q-icon name="history" class="detail-icon" />
              <div class="detail-content">
                <div class="detail-label">Memory Window</div>
                <div class="detail-value">{{ selectedPersona.memory_window }} messages</div>
              </div>
            </div>

            <div class="detail-row">
              <q-icon name="groups" class="detail-icon" />
              <div class="detail-content">
                <div class="detail-label">Max Agents per Turn</div>
                <div class="detail-value">{{ selectedPersona.max_agents_per_turn }}</div>
              </div>
            </div>
          </div>
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="Close" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- User Persona Dialog -->
    <q-dialog v-model="showUserPersonaDialog">
      <q-card style="min-width: 450px">
        <q-card-section class="bg-gradient-primary text-white">
          <div class="text-h6">
            <q-icon name="badge" class="q-mr-sm" />
            Your Roleplay Persona
          </div>
          <div class="text-caption">
            Define who you are in this conversation
          </div>
        </q-card-section>

        <q-card-section>
          <q-input
            v-model="userPersonaInput"
            outlined
            autogrow
            type="textarea"
            label="Describe your character"
            placeholder="e.g., A fearless space explorer seeking ancient artifacts..."
            hint="This helps agents understand your role in the roleplay"
            :maxlength="500"
            counter
            rows="4"
          >
            <template v-slot:prepend>
              <q-icon name="person" />
            </template>
          </q-input>

          <div class="q-mt-md">
            <div class="text-caption text-grey-7 q-mb-sm">Quick templates:</div>
            <div class="persona-templates">
              <q-chip
                v-for="template in personaTemplates"
                :key="template.value"
                clickable
                @click="userPersonaInput = template.label"
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
          <q-btn flat label="Clear" color="negative" @click="clearUserPersona" v-if="userPersona" />
          <q-btn flat label="Cancel" color="grey" v-close-popup />
          <q-btn
            flat
            label="Save"
            color="primary"
            @click="saveUserPersona"
            :disable="!userPersonaInput.trim()"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar, QScrollArea } from 'quasar'
import { getMessages, sendMessage, getPersonas, type Message, type Persona, authState } from '../api'
import { useWebSocket, createChatWebSocketUrl, type WebSocketMessage } from '../websocket'

const $q = useQuasar()
const route = useRoute()
const router = useRouter()
const sessionId = route.params.id as string

// Refs
const messages = ref<MessageWithLoading[]>([])
const availablePersonas = ref<Persona[]>([])
const selectedPersonas = ref<string[]>([])
const loading = ref(false)
const sending = ref(false)
const inputValue = ref('')
const scrollArea = ref<InstanceType<typeof QScrollArea> | null>(null)
const inputRef = ref<any>(null)

// Dialog states
const showAgentDialog = ref(false)
const showTemplatesDialog = ref(false)
const showAttachmentDialog = ref(false)
const showPersonaDialog = ref(false)
const showUserPersonaDialog = ref(false)
const selectedPersona = ref<Persona | null>(null)
const agentSearchQuery = ref('')

// User persona
const userPersona = ref<string>('')
const userPersonaInput = ref<string>('')

// Attachment handling
const newAttachment = ref<File[] | null>(null)
const attachedFiles = ref<File[]>([])

interface MessageWithLoading extends Message {
  loading?: boolean
  feedback?: 'positive' | 'negative'
}

// Message templates
const messageTemplates = [
  { title: 'Request Summary', content: 'Please provide a concise summary of the above discussion.' },
  { title: 'Ask for Details', content: 'Can you elaborate more on this topic?' },
  { title: 'Request Examples', content: 'Could you give me some concrete examples?' },
  { title: 'Ask for Comparison', content: 'What are the pros and cons of different approaches?' },
  { title: 'Next Steps', content: 'What should I do next based on this information?' },
  { title: 'Simplify', content: 'Can you explain this in simpler terms?' },
]

// Quick prompts
const quickPrompts = [
  { value: 'help', label: 'What can you help me with?' },
  { value: 'agents', label: 'Show available agents' },
  { value: 'example', label: 'Give me an example' },
]

const simplePrompts = [
  { value: 'continue', label: 'Continue' },
  { value: 'clarify', label: 'Please clarify' },
  { value: 'more', label: 'Tell me more' },
]

const personaTemplates = [
  { value: 'hero', label: 'A fearless hero on a quest' },
  { value: 'detective', label: 'A sharp-minded detective' },
  { value: 'merchant', label: 'A cunning merchant' },
  { value: 'scholar', label: 'A wise scholar' },
  { value: 'adventurer', label: 'A curious adventurer' },
]

// Agent colors for visual distinction
const agentColorMap = new Map<string, string>()
const agentColors = ['#5e7ce0', '#3ac295', '#f66f6a', '#ffa500', '#9747ff', '#00bcd4', '#e91e63', '#4caf50']

// Computed
const personaOptions = computed(() => {
  return availablePersonas.value.map(p => ({
    label: `${p.name} (@${p.handle})`,
    value: p.handle
  }))
})

const filteredPersonas = computed(() => {
  if (!agentSearchQuery.value.trim()) {
    return availablePersonas.value
  }
  const query = agentSearchQuery.value.toLowerCase()
  return availablePersonas.value.filter(p =>
    p.name.toLowerCase().includes(query) ||
    p.handle.toLowerCase().includes(query) ||
    p.tone.toLowerCase().includes(query)
  )
})

// WebSocket handlers
const handleAgentStart = (data: any) => {
  const agentMessage: MessageWithLoading = {
    id: data.message_id || `agent-${Date.now()}`,
    sender: data.sender || 'agent',
    content: '',
    timestamp: data.timestamp || new Date().toISOString(),
    loading: true
  }
  messages.value.push(agentMessage)
  nextTick(() => scrollToBottom())
}

const handleAgentChunk = (data: any) => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    const msg = messages.value[i]
    if (msg && msg.loading && msg.sender !== 'user') {
      msg.content += (data.content || data.text || data)
      nextTick(() => scrollToBottom())
      break
    }
  }
}

const handleAgentEnd = (data: any) => {
  for (let i = messages.value.length - 1; i >= 0; i--) {
    const msg = messages.value[i]
    if (msg && msg.loading && (msg.id === data.message_id || msg.sender !== 'user')) {
      msg.loading = false
      if (data.content) {
        msg.content = data.content
      }
      break
    }
  }
}

const handleNewMessage = (data: any) => {
  const newMessage: MessageWithLoading = {
    id: data.id,
    sender: data.sender,
    content: data.content,
    timestamp: data.timestamp
  }
  messages.value.push(newMessage)
  nextTick(() => scrollToBottom())
}

const handleWebSocketMessage = (message: WebSocketMessage) => {
  console.log('Processing WebSocket message:', message)
  
  switch (message.event) {
    case 'agent.chunk':
      handleAgentChunk(message.data)
      break
    case 'agent.start':
      handleAgentStart(message.data)
      break
    case 'agent.end':
      handleAgentEnd(message.data)
      break
    case 'message.new':
      handleNewMessage(message.data)
      break
    default:
      console.log('Unknown message event:', message.event)
  }
}

// WebSocket connection
const wsUrl = createChatWebSocketUrl(sessionId)
const { connect: connectWebSocket } = useWebSocket({
  url: wsUrl,
  reconnect: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  onMessage: handleWebSocketMessage,
  onOpen: () => console.log('WebSocket connected to session:', sessionId),
  onClose: () => console.log('WebSocket disconnected from session:', sessionId),
  onError: (error) => console.error('WebSocket error:', error)
})

// Methods
const loadData = async () => {
  loading.value = true
  try {
    const [msgs, personas] = await Promise.all([
      getMessages(sessionId),
      getPersonas(authState.tenantId)
    ])
    // 处理 API 可能返回对象包含数组的情况
    const msgsData: any = msgs
    const messageArray = Array.isArray(msgs) ? msgs : (msgsData?.messages || [])
    messages.value = messageArray.map((m: Message) => ({ ...m, feedback: undefined }))
    availablePersonas.value = personas
    
    // 获取用户画像
    if (msgsData?.user_persona) {
      userPersona.value = msgsData.user_persona
      userPersonaInput.value = msgsData.user_persona
    }
    
    await nextTick()
    scrollToBottom()
  } catch (e) {
    console.error('Failed to load chat data:', e)
    $q.notify({ type: 'negative', message: 'Failed to load conversation' })
  } finally {
    loading.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (scrollArea.value) {
      const scrollTarget = scrollArea.value.getScrollTarget()
      scrollArea.value.setScrollPosition('vertical', scrollTarget.scrollHeight, 300)
    }
  })
}

const handleKeyDown = (event: KeyboardEvent) => {
  // Detect @ symbol to open agent mention
  if (event.key === '@') {
    nextTick(() => {
      openAgentMention()
    })
  }
}

const handlePromptClick = (item: any) => {
  inputValue.value = item.label
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
    }
  })
}

const handleSubmit = async () => {
  const messageContent = inputValue.value.trim()
  if (!messageContent) return

  // Check if any personas are selected
  if (selectedPersonas.value.length === 0) {
    $q.notify({
      type: 'warning',
      message: 'Please select at least one target agent.',
      position: 'top',
      timeout: 2500
    })
    return
  }
  
  sending.value = true
  const targets = selectedPersonas.value

  // Optimistic UI update
  messages.value.push({
    id: 'temp-' + Date.now(),
    sender: 'user',
    content: messageContent,
    timestamp: new Date().toISOString()
  })
  
  inputValue.value = ''
  attachedFiles.value = []
  await nextTick()
  scrollToBottom()

  try {
    await sendMessage(sessionId, messageContent, targets)
  } catch (e) {
    console.error('Failed to send message:', e)
    $q.notify({ type: 'negative', message: 'Failed to send message' })
    messages.value = messages.value.filter(m => !m.id.toString().startsWith('temp-'))
  } finally {
    sending.value = false
  }
}

const goBack = () => {
  router.push('/sessions')
}

// Agent color management
const getAgentColor = (agentName: string | undefined): string => {
  const name = agentName || 'unknown'
  if (!agentColorMap.has(name)) {
    const colorIndex = agentColorMap.size % agentColors.length
    const color = agentColors[colorIndex] || '#5e7ce0'
    agentColorMap.set(name, color)
  }
  return agentColorMap.get(name) || agentColors[0] || '#5e7ce0'
}

const getAgentInitial = (agentName: string | undefined): string => {
  return agentName ? agentName.charAt(0).toUpperCase() : 'A'
}

// Message actions
const copyMessage = (content: string) => {
  navigator.clipboard.writeText(content).then(() => {
    $q.notify({
      type: 'positive',
      message: 'Message copied to clipboard',
      position: 'top',
      timeout: 1500
    })
  }).catch(() => {
    $q.notify({
      type: 'negative',
      message: 'Failed to copy message',
      position: 'top'
    })
  })
}

const feedbackMessage = (messageId: string, type: 'positive' | 'negative') => {
  const msg = messages.value.find(m => m.id === messageId)
  if (msg) {
    msg.feedback = msg.feedback === type ? undefined : type
    // TODO: Send feedback to backend
    $q.notify({
      type: 'info',
      message: `Feedback recorded: ${type === 'positive' ? '👍' : '👎'}`,
      position: 'top',
      timeout: 1500
    })
  }
}

const showPersonaDetails = (agentName: string | undefined) => {
  if (!agentName) return
  const persona = availablePersonas.value.find(p => p.handle === agentName || p.name === agentName)
  if (persona) {
    selectedPersona.value = persona
    showPersonaDialog.value = true
  }
}

// Agent mention
const openAgentMention = () => {
  agentSearchQuery.value = ''
  showAgentDialog.value = true
}

const mentionAgent = (persona: Persona) => {
  inputValue.value += `@${persona.handle} `
  showAgentDialog.value = false
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
    }
  })
}

// Templates
const openTemplates = () => {
  showTemplatesDialog.value = true
}

const applyTemplate = (content: string) => {
  inputValue.value = content
  showTemplatesDialog.value = false
  nextTick(() => {
    if (inputRef.value) {
      inputRef.value.focus()
    }
  })
}

// Attachments
const openAttachment = () => {
  showAttachmentDialog.value = true
}

const attachFiles = () => {
  if (newAttachment.value && newAttachment.value.length > 0) {
    attachedFiles.value.push(...newAttachment.value)
    newAttachment.value = null
    showAttachmentDialog.value = false
    $q.notify({
      type: 'positive',
      message: `${attachedFiles.value.length} file(s) attached`,
      position: 'top',
      timeout: 1500
    })
  }
}

const removeAttachment = (index: number) => {
  attachedFiles.value.splice(index, 1)
}

// User persona management
const openUserPersonaDialog = () => {
  userPersonaInput.value = userPersona.value
  showUserPersonaDialog.value = true
}

const saveUserPersona = async () => {
  const newPersona = userPersonaInput.value.trim()
  if (!newPersona) return

  try {
    // 调用 API 更新用户画像
    await fetch(`/api/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_persona: newPersona })
    })

    userPersona.value = newPersona
    showUserPersonaDialog.value = false
    $q.notify({
      type: 'positive',
      message: 'Your roleplay persona has been updated',
      position: 'top',
      timeout: 2000
    })
  } catch (e) {
    console.error('Failed to update user persona:', e)
    $q.notify({
      type: 'negative',
      message: 'Failed to save persona',
      position: 'top'
    })
  }
}

const clearUserPersona = async () => {
  try {
    await fetch(`/api/sessions/${sessionId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ user_persona: null })
    })

    userPersona.value = ''
    userPersonaInput.value = ''
    showUserPersonaDialog.value = false
    $q.notify({
      type: 'info',
      message: 'Roleplay persona cleared',
      position: 'top',
      timeout: 2000
    })
  } catch (e) {
    console.error('Failed to clear user persona:', e)
    $q.notify({
      type: 'negative',
      message: 'Failed to clear persona',
      position: 'top'
    })
  }
}

// Utilities
const formatTime = (timestamp: string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  loadData()
  connectWebSocket()
})
</script>

<style scoped>
.chat-conversation-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--color-background);
  font-family: var(--font-body);
}

/* Header */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: var(--color-surface);
  border-bottom: var(--border-width) solid var(--color-muted, #e0e0e0);
  box-shadow: var(--shadow, 0 2px 4px rgba(0,0,0,0.05));
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-title {
  display: flex;
  flex-direction: column;
}

.title-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  font-family: var(--font-heading);
}

.active-agents {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-muted);
  margin-top: 2px;
}

.bg-gradient-primary {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
}

/* Messages Container */
.messages-container {
  flex: 1;
  padding: 16px 24px;
  background: var(--color-background);
}

.loading-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 16px;
  color: var(--color-muted);
}

.empty-state h5 {
  margin: 8px 0;
  color: var(--color-text);
  font-family: var(--font-heading);
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  max-width: 600px;
  margin-top: 16px;
}

/* Messages List */
.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  animation: fadeIn 0.3s ease-in;
}

.message-row.message-user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
}

.message-user .message-content-wrapper {
  align-items: flex-end;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
}

.agent-name {
  font-weight: 600;
  font-size: 13px;
  color: var(--color-text);
  cursor: pointer;
  font-family: var(--font-body);
}

.agent-name:hover {
  text-decoration: underline;
  color: var(--color-primary);
}

.message-time {
  font-size: 11px;
  color: var(--color-muted);
}

.message-bubble {
  padding: 12px 16px;
  border-radius: var(--border-radius, 12px);
  word-wrap: break-word;
}

.bubble-user {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-accent) 100%);
  color: var(--color-surface);
  border-bottom-right-radius: 4px;
}

.bubble-agent {
  background: var(--color-surface);
  color: var(--color-text);
  border: var(--border-width) solid var(--color-muted, #e0e0e0);
  border-bottom-left-radius: 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--color-muted);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-10px); }
}

.message-text {
  line-height: 1.5;
  white-space: pre-wrap;
  font-family: var(--font-body);
}

.message-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  padding: 0 8px;
}

.message-row:hover .message-actions {
  opacity: 1;
}

.quick-actions {
  display: flex;
  gap: 8px;
  padding: 12px 0;
  border-top: var(--border-width) solid var(--color-muted, #e0e0e0);
  margin-top: 16px;
}

/* Input Container */
.input-container {
  background: var(--color-surface);
  border-top: var(--border-width) solid var(--color-muted, #e0e0e0);
  padding: 12px 24px 16px;
}

.attached-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.input-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.message-input {
  flex: 1;
}

.char-counter {
  font-size: 12px;
  color: var(--color-muted);
  padding-bottom: 8px;
  flex-shrink: 0;
}

/* Persona Details */
.persona-details {
  padding: 8px 0;
}

.detail-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.detail-icon {
  color: var(--color-primary);
  font-size: 20px;
  margin-top: 2px;
}

.detail-content {
  flex: 1;
}

.detail-label {
  font-size: 12px;
  color: var(--color-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.detail-value {
  font-size: 14px;
  color: var(--color-text);
  line-height: 1.5;
  font-family: var(--font-body);
}

/* Dialog Items */
.agent-list-item,
.template-item {
  transition: background 0.2s;
}

.agent-list-item:hover,
.template-item:hover {
  background: var(--color-background);
}

/* Animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* User Persona Templates */
.persona-templates {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Responsive */
@media (max-width: 768px) {
  .chat-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .message-content-wrapper {
    max-width: 85%;
  }

  .input-row {
    flex-wrap: wrap;
  }

  .char-counter {
    order: -1;
    width: 100%;
    text-align: right;
    padding-bottom: 4px;
  }
}
</style>