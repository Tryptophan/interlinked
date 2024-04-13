import { useCallback, useState } from "react";
import "./App.css";
import { LiveTranscriptionEvents, createClient } from "@deepgram/sdk";
import OpenAI from "openai";

const deepgram = createClient(import.meta.env.VITE_DEEPGRAM_API_KEY!);
const openai = new OpenAI({
  apiKey: import.meta.env.VITE_OPENAI_API_KEY!,
  dangerouslyAllowBrowser: true,
});

function App() {
  const [sourceLanguage, setSourceLanguage] = useState("en-US");
  const [targetLanguage, setTargetLanguage] = useState("zh");

  const [sourceTranscript, setSourceTranscript] = useState<string[]>([]);
  const [targetTranscript, setTargetTranscript] = useState<string[]>([]);

  const listen = useCallback(() => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const connection = deepgram.listen.live({
        model: "base",
        language: sourceLanguage,
        smart_format: true,
      });

      connection.addListener(LiveTranscriptionEvents.Open, () => {
        console.log("dg onopen");
        connection.addListener(
          LiveTranscriptionEvents.Transcript,
          async (data) => {
            const text = data.channel.alternatives[0]?.transcript;
            if (text && text.length) {
              console.log(text);
              setSourceTranscript((prevState) => [...prevState, text]);
              // Translate
              const llmResponse = await openai.chat.completions.create({
                messages: [
                  {
                    role: "system",
                    content: `You will be provided with a sentence in ${sourceLanguage}, and your task is to translate it into ${targetLanguage}.`,
                  },
                  { role: "user", content: text },
                ],
                model: "gpt-3.5-turbo",
              });

              const translation = llmResponse.choices[0].message.content;
              if (translation) {
                setTargetTranscript((prevState) => [...prevState, translation]);
              }
              // TODO: Cultural context
            }
          }
        );
      });
      connection.addListener("error", (error) => console.log({ error }));

      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0 && connection.getReadyState() === 1) {
          connection.send(event.data);
        }
      };
      recorder.start(500);
    });
  }, [sourceLanguage, targetLanguage]);

  return (
    <>
      <div className="App">
        Source Language:
        <select
          value={sourceLanguage}
          onChange={(event) => setSourceLanguage(event.target.value)}
        >
          <option value="en-US">English</option>
          <option value="zh">Chinese</option>
        </select>
        Target Language:
        <select
          value={targetLanguage}
          onChange={(event) => setTargetLanguage(event.target.value)}
        >
          <option value="en-US">English</option>
          <option value="zh">Chinese</option>
        </select>
        <button onClick={listen}>Listen</button>
        Source Transcript:
        <div>{sourceTranscript.join(" ")}</div>
        Target Transcript:
        <div>{targetTranscript.join(" ")}</div>
      </div>
    </>
  );
}

export default App;
