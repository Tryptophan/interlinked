import { useCallback, useState } from "react";
import "./App.css";
import { LiveTranscriptionEvents, createClient } from "@deepgram/sdk";
import OpenAI from "openai";
import { FaMicrophone } from "react-icons/fa";

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

  const translate = useCallback(
    async (from: string, to: string, text: string) => {
      try {
        const response = await fetch(
          "https://interlinked.auto.movie/api/translate",
          {
            method: "POST",
            headers: {
              Accept: "application/json",
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              from_lang: from,
              to_lang: to,
              text: text,
            }),
          }
        );

        if (!response.ok) {
          throw new Error("Failed to fetch data");
        }

        return (await response.json()).translated_text;
      } catch (error) {
        console.error("Error:", error);
      }
    },
    []
  );

  const generateCulturalContext = useCallback(
    async (text: string, language: string) => {
      const contextResponse = await openai.chat.completions.create({
        messages: [
          {
            role: "system",
            content: `You will be provided with text in language ${language}, your task is to return an explanation of a famous person/place/thing (if none found, reply only with ##NO_REPLY##) from the text in the language ${language}. Keep your response to 1 short sentence.`,
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
              const translation = await translate(
                sourceLanguage,
                targetLanguage,
                text
              );
              if (translation) {
                setTargetTranscript((prevState) => [...prevState, translation]);
                // Generate cultural context
                await generateCulturalContext(translation, targetLanguage);
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
        <h1>Try Interlinked AI</h1>
        <h2>
          AI-powered live and real-time speech translation across 100+ languages
          with cultural context explanation, perfect for meetings, calls,
          videos, webinars, and conferences.
        </h2>
        <div className="Translator">
          <div className="Left">
            <div className="Step">
              Step 1: Select source and target languages
            </div>
            <div className="LanguageSelect">
              Translate From
              <select
                value={sourceLanguage}
                onChange={(event) => setSourceLanguage(event.target.value)}
              >
                <option value="en-US">English</option>
                <option value="zh">Chinese</option>
              </select>
            </div>
            <div className="LanguageSelect">
              Translate To
              <select
                value={targetLanguage}
                onChange={(event) => setTargetLanguage(event.target.value)}
              >
                <option value="en-US">English</option>
                <option value="zh">Chinese</option>
              </select>
            </div>
            <div className="Step">
              Step 2: Enable the Microphone and speak in your own language
            </div>
            <FaMicrophone
              style={{ color: !listening ? "black" : "red" }}
              className="MicToggle"
              onClick={listen}
            />
          </div>
          <div className="Right">
            <div className="Step">
              Step 3: View the live transcription and translation in 100+
              different languages
            </div>
            <div className="Transcripts">
              {!sourceTranscript.length || !targetTranscript.length ? (
                "Translator is starting..."
              ) : (
                <>
                  <div>{sourceTranscript.join(" ")}</div>
                  <div>{targetTranscript.join(" ")}</div>
                </>
              )}
            </div>
          </div>
          <div>
            <div className="Step">
              Step 4: See the cultural explanation for understanding
            </div>
            {contexts.map((context, index) => (
              <div key={index}>{context.text}</div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

export default App;
