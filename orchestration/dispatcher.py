"""
orchestration/dispatcher.py

Kronos'un "beyin sapı". Bir kullanıcı mesajı geldiğinde:
  1. Hafızaya ekler
  2. Modele gönderir
  3. Model bir araç çağırmak isterse aracı çalıştırır ve sonucu modele geri verir
  4. Model son metin yanıtını verene kadar bu döngüyü tekrarlar

Faz 1'de tek bir model + tek bir hafıza + araç kaydı var. Birden fazla
"uzman ekip" (teams/) devreye girdiğinde bu dosya, işi hangi ekibe
yönlendireceğine karar veren bir router'a dönüşecek — ama o iş, gerçek
ihtiyaç ortaya çıkınca yapılacak.
"""

from core.memory.short_term import ShortTermMemory
from core.models.interface import ModelAdapter
from core.tools.registry import ToolRegistry


class Dispatcher:
    def __init__(
        self,
        model: ModelAdapter,
        tools: ToolRegistry,
        system_prompt: str = "",
        max_tool_iterations: int = 5,
    ):
        self.model = model
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_tool_iterations = max_tool_iterations
        self.memory = ShortTermMemory()

    def handle_message(self, user_input: str) -> str:
        self.memory.add_user_message(user_input)

        for _ in range(self.max_tool_iterations):
            response = self.model.complete(
                messages=self.memory.get_messages(),
                system=self.system_prompt,
                tools=self.tools.as_anthropic_tools() if self.tools.list_names() else None,
            )

            if not response.tool_calls:
                self.memory.add_assistant_message(response.text)
                return response.text

            # Model bir veya daha fazla araç çağırmak istedi.
            assistant_blocks = []
            if response.text:
                assistant_blocks.append({"type": "text", "text": response.text})
            for call in response.tool_calls:
                assistant_blocks.append(
                    {
                        "type": "tool_use",
                        "id": call.call_id,
                        "name": call.name,
                        "input": call.arguments,
                    }
                )
            self.memory.add_raw({"role": "assistant", "content": assistant_blocks})

            tool_result_blocks = []
            for call in response.tool_calls:
                try:
                    result = self.tools.execute(call.name, call.arguments)
                    content = str(result)
                except Exception as exc:  # araç hata verirse modele bildir, çökme
                    content = f"HATA: {exc}"

                tool_result_blocks.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": call.call_id,
                        "content": content,
                    }
                )
            self.memory.add_raw({"role": "user", "content": tool_result_blocks})

        return "Kronos: araç döngüsü sınırına ulaşıldı, işlemi tamamlayamadım."
