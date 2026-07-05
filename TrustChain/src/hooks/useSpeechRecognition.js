import { useRef, useState } from "react";

export default function useSpeechRecognition() {

    const [text, setText] = useState("");

    const recognitionRef = useRef(null);

    if (!recognitionRef.current) {

        const SpeechRecognition =
            window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
            return {
                text,
                start: () => {},
                stop: () => {}
            };
        }

        const recognition = new SpeechRecognition();

        recognition.lang = "ko-KR";
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (e) => {

            let t = "";

            for (let i = 0; i < e.results.length; i++) {
                t += e.results[i][0].transcript;
            }

            setText(t);

        };

        recognitionRef.current = recognition;

    }

    return {

        text,

        start: () => recognitionRef.current.start(),

        stop: () => recognitionRef.current.stop()

    };

}