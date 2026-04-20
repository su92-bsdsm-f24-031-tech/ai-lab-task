const chatWindow = document.getElementById("chatWindow");
const chatForm = document.getElementById("chatForm");
const userInput = document.getElementById("userInput");

function appendMessage(role, text, meta = "", matches = []) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);

  if (meta) {
    const detail = document.createElement("small");
    detail.className = "meta";
    detail.textContent = meta;
    wrapper.appendChild(detail);
  }

  if (role === "bot" && matches.length > 0) {
    const list = document.createElement("ul");
    list.className = "matches";

    matches.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = `Q: ${item.question} | score: ${item.score}`;
      list.appendChild(li);
    });

    wrapper.appendChild(list);
  }

  chatWindow.appendChild(wrapper);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = userInput.value.trim();
  if (!message) {
    return;
  }

  appendMessage("user", message);
  userInput.value = "";
  userInput.focus();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      appendMessage("bot", data.reply || "Something went wrong.");
      return;
    }

    const meta =
      data.best_match_question && data.best_match_score !== undefined
        ? `best match: ${data.best_match_question} | similarity: ${data.best_match_score}`
        : "";

    appendMessage("bot", data.reply, meta, data.matches || []);
  } catch (error) {
    appendMessage("bot", `Error: ${error.message}`);
  }
});
