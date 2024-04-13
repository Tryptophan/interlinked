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
  const [listening, setListening] = useState(false);

  const [sourceLanguage, setSourceLanguage] = useState("en-US");
  const [targetLanguage, setTargetLanguage] = useState("zh");

  const [sourceTranscript, setSourceTranscript] = useState<string[]>([]);
  const [targetTranscript, setTargetTranscript] = useState<string[]>([]);

  const [contexts, setContexts] = useState<{ image?: string; text: string }[]>(
    []
  );

  const generateCulturalContext = useCallback(
    async (text: string, language: string) => {
      const contextResponse = await openai.chat.completions.create({
        messages: [
          {
            role: "system",
            content: `You will be provided with text in language ${language}, your task is to return an explanation of a famous person/place/thing (if none found, reply only with ##NO_REPLY##) from the text in the language ${language}. Keep your response to 2 sentences.`,
          },
          { role: "user", content: text },
        ],
        model: "gpt-4-turbo",
      });

      const context = contextResponse.choices[0].message.content;
      if (!context || !context.length || context === "##NO_REPLY##") {
        console.log("Got no reply for context");
        return;
      }

      console.log("generated context", context);

      setContexts((prevState) => [...prevState, { text: context }]);
    },
    []
  );

  // useEffect(() => {
  //   (window as any).test = async () => {
  //     await generateCulturalContext("昨天我去了长城。", "zh");
  //   };
  // }, []);

  const listen = useCallback(() => {
    if (listening) {
      return;
    }
    setListening(true);
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
              const translateResponse = await openai.chat.completions.create({
                messages: [
                  {
                    role: "system",
                    content: `You will be provided with a sentence in ${sourceLanguage}, and your task is to translate it into ${targetLanguage}.`,
                  },
                  { role: "user", content: text },
                ],
                model: "gpt-3.5-turbo",
              });

              const translation = translateResponse.choices[0].message.content;
              if (translation) {
                setTargetTranscript((prevState) => [...prevState, translation]);
                // Generate cultural context
                // await generateCulturalContext(translation, targetLanguage);
              }
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
        <div className="Left">
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
          <button onClick={listen}>{!listening ? "Start" : "Stop"}</button>
          Source Transcript:
          <div>{sourceTranscript.join(" ")}</div>
          Target Transcript:
          <div>{targetTranscript.join(" ")}</div>
        </div>
        <div className="Right">
          {contexts.map((context, index) => (
            <div key={index}>{context.text}</div>
          ))}
        </div>
      </div>
    </>
  );
}

export default App;
