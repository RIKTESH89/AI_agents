package io.shubham0204.smollmandroid.llm

import android.util.Log
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.smith.lai.langgraph4j_android_adapter.BuildConfig
import com.smith.lai.langgraph4j_android_adapter.httpclient.OkHttpClientBuilder
import dev.langchain4j.data.message.AiMessage
import dev.langchain4j.data.message.ChatMessage
import dev.langchain4j.data.message.SystemMessage
import dev.langchain4j.data.message.ToolExecutionResultMessage
import dev.langchain4j.data.message.UserMessage
import dev.langchain4j.model.chat.ChatLanguageModel
import dev.langchain4j.model.ollama.OllamaChatModel
import dev.langchain4j.model.openai.OpenAiChatModel
import io.shubham0204.smollm.SmolLM
import io.shubham0204.smollmandroid.data.Chat
import io.shubham0204.smollmandroid.data.MessagesDB
import io.shubham0204.smollmandroid.ui.screens.chat.ChatScreenViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.bsc.langgraph4j.CompiledGraph
import org.bsc.langgraph4j.RunnableConfig
import org.bsc.langgraph4j.StateGraph
import org.bsc.langgraph4j.agentexecutor.AgentExecutor
import org.bsc.langgraph4j.prebuilt.ToolNode
import org.koin.core.annotation.Single
import java.lang.reflect.Type
import java.time.Duration
import kotlin.time.measureTime

private const val LOGTAG = "[SmolLMManager-Kt]"
private val LOGD: (String) -> Unit = { Log.d(LOGTAG, it) }
private val LOGE: (String, Throwable) -> Unit = { msg, tr -> Log.e(LOGTAG, msg, tr) }

// Define a new state for the multi-agent graph
class SupervisorState(
    val messages: MutableList<ChatMessage> = mutableListOf(),
    var next: String? = null
) {
    fun finalResponse(): String? {
        return messages.lastOrNull { it is AiMessage && !it.hasToolExecutionRequests() }?.text()
    }
}

@Single
class SmolLMManager(
    private val messagesDB: MessagesDB,
) {
    private val instance = SmolLM()
    private var responseGenerationJob: Job? = null
    private var modelInitJob: Job? = null
    private var chat: Chat? = null
    private lateinit var viewModel: ChatScreenViewModel
    private var compiledSupervisorGraph: CompiledGraph<SupervisorState>? = null
    // --- CHANGE THIS LINE TO SWITCH MODELS ---
    // "openai": Uses the OpenAI API (requires API key)
    // "ollama": Uses a local Ollama server (requires Ollama to be running)
    // "local": Uses the on-device GGUF model (not supported for agentic features)
    private val TEST_MODE = "openai"
    private var openai: OpenAiChatModel? = null
    private var ollama: OllamaChatModel? = null

    private var isInstanceLoaded = false
    var isInferenceOn = false

    data class SmolLMInitParams(
        val chat: Chat,
        val modelPath: String,
        val minP: Float,
        val temperature: Float,
        val storeChats: Boolean,
        val contextSize: Long,
        val chatTemplate: String,
        val nThreads: Int,
        val useMmap: Boolean,
        val useMlock: Boolean,
    )

    data class SmolLMResponse(
        val response: String,
        val generationSpeed: Float,
        val generationTimeSecs: Int,
        val contextLengthUsed: Int,
    )

    fun setViewModel(_viewModel: ChatScreenViewModel) {
        viewModel = _viewModel
    }

    private fun getModel(): ChatLanguageModel {
        return when (TEST_MODE) {
            "openai" -> {
                if (openai == null) {
                    LOGD("Initializing OpenAI model...")
                    val httpClientBuilder = OkHttpClientBuilder()
                    httpClientBuilder.connectTimeout(Duration.ofSeconds(30))
                        .readTimeout(Duration.ofSeconds(120))
                    openai = OpenAiChatModel.builder()
                        // IMPORTANT: Make sure your OPENAI_API_KEY is set in the
                        // langgraph4j-android-adapter/build.gradle.kts file
                        .apiKey(BuildConfig.OPENAI_API_KEY)
                        .baseUrl("https://api.openai.com/v1")
                        .httpClientBuilder(httpClientBuilder)
                        .modelName("gpt-4o-mini")
                        .temperature(0.0)
                        .maxTokens(2000)
                        .maxRetries(2)
                        .logRequests(true)
                        .logResponses(true)
                        .build()
                }
                openai!!
            }
            "ollama" -> {
                if (ollama == null) {
                    LOGD("Initializing Ollama model...")
                    val httpClientBuilder = OkHttpClientBuilder()
                    httpClientBuilder.connectTimeout(Duration.ofSeconds(30))
                        .readTimeout(Duration.ofSeconds(120))
                    ollama = OllamaChatModel.builder()
                        .baseUrl(BuildConfig.OLLAMA_URL)
                        .httpClientBuilder(httpClientBuilder)
                        .temperature(0.0)
                        .logRequests(true)
                        .logResponses(true)
                        .modelName("llama3.1:latest")
                        .build()
                }
                ollama!!
            }
            else -> {
                // The local model does not support the advanced function calling needed for this agent setup.
                throw IllegalStateException("Local model is not supported for this agentic setup yet.")
            }
        }
    }

    fun setupSupervisorGraph() {
        try {
            LOGD("Setting up supervisor graph...")
            val model = getModel()

            // 1. Create Specialist Agent and Tool Nodes
            val mathAgent = createMathAgent(model)
            val emailAgent = createEmailAgent(model)
            val mathTools = createMathToolNode()

            // 2. Define Graph State
            val workflow = StateGraph(SupervisorState::class.java)

            // 3. Define Nodes
            workflow.addNode("math_agent") { state ->
                val agentState = AgentExecutor.State(state.messages)
                val result = mathAgent.execute(agentState)
                SupervisorState(result.messages.toMutableList())
            }
            workflow.addNode("email_agent") { state ->
                val agentState = AgentExecutor.State(state.messages)
                val result = emailAgent.execute(agentState)
                SupervisorState(result.messages.toMutableList())
            }
            workflow.addNode("math_tools") { state ->
                val toolState = AgentExecutor.State(state.messages)
                val result = mathTools.execute(toolState)
                SupervisorState(result.messages.toMutableList())
            }

            // 4. Define Supervisor Logic
            val members = listOf("math_agent", "email_agent")
            val systemPrompt = "You are a supervisor. Given the user request, select the next agent to act: ${members.joinToString(", ")}. " +
                    "If the previous agent was 'math_agent', you must check if the user's request is now satisfied. If it is, respond with 'FINISH'. " +
                    "Otherwise, route to another agent or call a tool if necessary. " +
                    "Respond with a JSON object with a single key 'next' and a value of the agent name, 'FINISH', or 'math_tools'."

            workflow.addNode("supervisor") { state ->
                LOGD("SUPERVISOR: Deciding next step...")
                val supervisorMessages = mutableListOf<ChatMessage>(SystemMessage.from(systemPrompt))
                supervisorMessages.addAll(state.messages)

                val response = model.generate(supervisorMessages)
                val responseText = response.content().text()

                val gson = Gson()
                val type: Type = object : TypeToken<Map<String, String>>() {}.type
                try {
                    val result: Map<String, String> = gson.fromJson(responseText, type)
                    state.next = result["next"]
                } catch (e: Exception) {
                    LOGE("Supervisor failed to parse JSON, defaulting to FINISH", e)
                    state.next = "FINISH" // Fallback
                }
                state
            }

            // 5. Wire the graph
            workflow.addEdge("math_agent", "supervisor")
            workflow.addEdge("email_agent", "supervisor")
            workflow.addEdge("math_tools", "supervisor")

            workflow.addConditionalEdges(
                "supervisor",
                { state -> state.next!! },
                StateGraph.EdgeMapping<SupervisorState>()
                    .add("math_agent", "math_agent")
                    .add("email_agent", "email_agent")
                    .add("math_tools", "math_tools")
                    .add("FINISH", StateGraph.END)
            )

            workflow.setEntryPoint("supervisor")

            // 6. Compile the graph
            compiledSupervisorGraph = workflow.compile()
            LOGD("Supervisor graph compiled successfully.")

        } catch (e: Exception) {
            LOGE("Failed to set up supervisor graph", e)
            throw e // Re-throw to be caught by the caller
        }
    }


    fun create(
        initParams: SmolLMInitParams,
        onError: (Exception) -> Unit,
        onSuccess: () -> Unit,
    ) {
        // This function is for the local GGUF model.
        // When using OpenAI, this setup is not required, but we'll leave it for potential future use.
        if (TEST_MODE != "local") {
            onSuccess()
            return
        }
        try {
            modelInitJob =
                CoroutineScope(Dispatchers.Default).launch {
                    chat = initParams.chat
                    if (isInstanceLoaded) {
                        close()
                    }
                    instance.create(
                        initParams.modelPath,
                        initParams.minP,
                        initParams.temperature,
                        initParams.storeChats,
                        initParams.contextSize,
                        initParams.chatTemplate,
                        initParams.nThreads,
                        initParams.useMmap,
                        initParams.useMlock,
                    )
                    LOGD("Model loaded")
                    if (initParams.chat.systemPrompt.isNotEmpty()) {
                        instance.addSystemPrompt(initParams.chat.systemPrompt)
                        LOGD("System prompt added")
                    }
                    if (!initParams.chat.isTask) {
                        messagesDB.getMessagesForModel(initParams.chat.id).forEach { message ->
                            if (message.isUserMessage) {
                                instance.addUserMessage(message.message)
                            } else {
                                instance.addAssistantMessage(message.message)
                            }
                        }
                    }
                    withContext(Dispatchers.Main) {
                        isInstanceLoaded = true
                        onSuccess()
                    }
                }
        } catch (e: Exception) {
            LOGE("Failed during model creation", e)
            onError(e)
        }
    }

    fun getResponse(
        query: String,
        responseTransform: (String) -> String,
        onPartialResponseGenerated: (String) -> Unit,
        onSuccess: (SmolLMResponse) -> Unit,
        onCancelled: () -> Unit,
        onError: (Exception) -> Unit,
    ) {
        try {
            assert(chat != null) { "Please call SmolLMManager.create() first." }
            responseGenerationJob =
                CoroutineScope(Dispatchers.Default).launch {
                    try {
                        isInferenceOn = true
                        var finalResponse = ""
                        val duration =
                            measureTime {
                                // Setup the supervisor graph. This will throw on failure.
                                setupSupervisorGraph()

                                val config = RunnableConfig.builder()
                                    .threadId(chat!!.id.toString())
                                    .build()

                                val initialState = SupervisorState(mutableListOf(UserMessage.from(query)))

                                Log.i(LOGTAG, "Invoking supervisor with initial state: ${initialState.messages}")

                                val finalState = compiledSupervisorGraph!!.invoke(initialState, config)

                                finalResponse = finalState.finalResponse() ?: "No final response could be generated."
                            }

                        finalResponse = responseTransform(finalResponse)
                        messagesDB.addAssistantMessage(chat!!.id, finalResponse)
                        withContext(Dispatchers.Main) {
                            isInferenceOn = false
                            onSuccess(
                                SmolLMResponse(
                                    response = finalResponse,
                                    generationSpeed = instance.getResponseGenerationSpeed(),
                                    generationTimeSecs = duration.inWholeSeconds.toInt(),
                                    contextLengthUsed = instance.getContextLengthUsed(),
                                ),
                            )
                        }
                    } catch (e: CancellationException) {
                        LOGD("Response generation was cancelled.")
                        isInferenceOn = false
                        onCancelled()
                    } catch (e: Exception) {
                        LOGE("An error occurred during response generation", e)
                        isInferenceOn = false
                        withContext(Dispatchers.Main) {
                            onError(e)
                        }
                    }
                }
        } catch (e: Exception) {
             LOGE("A critical error occurred before starting the coroutine", e)
             onError(e)
        }
    }

    fun stopResponseGeneration() {
        responseGenerationJob?.let { cancelJobIfActive(it) }
    }

    fun close() {
        stopResponseGeneration()
        modelInitJob?.let { cancelJobIfActive(it) }
        instance.close()
        isInstanceLoaded = false
    }

    private fun cancelJobIfActive(job: Job) {
        if (job.isActive) {
            job.cancel()
        }
    }
}

