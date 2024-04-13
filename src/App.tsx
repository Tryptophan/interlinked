import { useCallback, useState } from "react";
import "./App.css";
import { LiveTranscriptionEvents, createClient } from "@deepgram/sdk";

const deepgram = createClient(import.meta.env.VITE_DEEPGRAM_API_KEY!);

function App() {
  const listen = useCallback(() => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      const connection = deepgram.listen.live({
        model: "base",
        language: "en-US",
        smart_format: true,
      });

      connection.addListener(LiveTranscriptionEvents.Open, () => {
        console.log("dg onopen");
        connection.addListener(LiveTranscriptionEvents.Transcript, (data) => {
          const text = data.channel.alternatives[0]?.transcript;
          if (text && text.length) {
            console.log(text);
            setTranscript((prevState) => prevState + " " + text);
          }
        });
      });
      connection.addListener("error", (error) => console.log({ error }));

      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0 && connection.getReadyState() === 1) {
          // TODO: Check dg ready state
          connection.send(event.data);
        }
      };
      recorder.start(500);
    });
  }, []);

  const [transcript, setTranscript] = useState("");

  return (
    <>
      <div className="App">
        <button onClick={listen}>Listen</button>
        {transcript}
      </div>
    </>
  );
}

export default App;
