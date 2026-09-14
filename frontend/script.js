const API_URL = "http://127.0.0.1:8000/chat";


const chatButton = document.getElementById("chat-button");
const chatWidget = document.getElementById("chat-widget");
const closeChat = document.getElementById("close-chat");

const messages = document.getElementById("messages");

const questionInput = document.getElementById("question-input");
const sendButton = document.getElementById("send-button");


// Open chatbot

chatButton.addEventListener("click", () => {

    chatWidget.style.display = "flex";

    chatButton.style.display = "none";

    questionInput.focus();
});


// Close chatbot

closeChat.addEventListener("click", () => {

    chatWidget.style.display = "none";

    chatButton.style.display = "block";
});


// Add message

function addMessage(text, type) {

    const message = document.createElement("div");

    message.className = `message ${type}-message`;

    const avatar = document.createElement("div");

    avatar.className = "message-avatar";

    avatar.textContent =
        type === "bot"
            ? "🧠"
            : "👤";


    const content = document.createElement("div");

    content.className = "message-content";

    content.textContent = text;


    message.appendChild(avatar);

    message.appendChild(content);

    messages.appendChild(message);


    messages.scrollTop = messages.scrollHeight;
}


// Send question

async function sendQuestion() {

    const question = questionInput.value.trim();


    if (!question) {
        return;
    }


    addMessage(question, "user");


    questionInput.value = "";

    sendButton.disabled = true;


    addMessage("Thinking... 🤔", "bot");


    try {

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                question: question
            })

        });


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );
        }


        const data = await response.json();


        // Remove "Thinking..."

        const botMessages =
            document.querySelectorAll(".bot-message");

        const thinkingMessage =
            botMessages[botMessages.length - 1];

        thinkingMessage.remove();


        // Add actual answer

        addMessage(data.answer, "bot");


    } catch (error) {

        console.error(error);


        const botMessages =
            document.querySelectorAll(".bot-message");

        const thinkingMessage =
            botMessages[botMessages.length - 1];

        if (thinkingMessage) {
            thinkingMessage.remove();
        }


        addMessage(
            "Sorry, I couldn't connect to the knowledge base.",
            "bot"
        );

    } finally {

        sendButton.disabled = false;

        questionInput.focus();
    }
}


// Send button

sendButton.addEventListener(
    "click",
    sendQuestion
);


// Enter key

questionInput.addEventListener(
    "keydown",
    (event) => {

        if (event.key === "Enter") {

            sendQuestion();
        }
    }
);