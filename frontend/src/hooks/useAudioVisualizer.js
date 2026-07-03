import { useEffect, useRef, useState } from "react";

export default function useAudioVisualizer(isScanning){
  const canvasRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const animationRef = useRef(null);
  const [error,setError]=useState(null);

  useEffect(()=>{
    if(!isScanning){
      cleanup();
      return;
    }
    start();
    return cleanup;
  },[isScanning]);

  async function start(){
    try{
      const stream = await navigator.mediaDevices.getUserMedia({audio:true});
      streamRef.current=stream;

      const ctx=new (window.AudioContext||window.webkitAudioContext)();
      audioCtxRef.current=ctx;

      const analyser=ctx.createAnalyser();
      analyser.fftSize=256;
      analyserRef.current=analyser;

      const source=ctx.createMediaStreamSource(stream);
      source.connect(analyser);

      draw();
    }catch(e){
      setError(e);
    }
  }

  function draw(){
    const canvas=canvasRef.current;
    const analyser=analyserRef.current;
    if(!canvas||!analyser)return;

    const c=canvas.getContext("2d");
    const data=new Uint8Array(analyser.frequencyBinCount);

    const render=()=>{
      analyser.getByteFrequencyData(data);
      canvas.width=canvas.offsetWidth;
      canvas.height=canvas.offsetHeight;

      c.clearRect(0,0,canvas.width,canvas.height);

      let x=0;
      const w=(canvas.width/data.length)*1.5;

      data.forEach(v=>{
        c.fillStyle="#1B6FEB";
        c.fillRect(x,canvas.height-v/2,w-1,v/2);
        x+=w;
      });

      animationRef.current=requestAnimationFrame(render);
    };
    render();
  }

  function cleanup(){
    if(animationRef.current) cancelAnimationFrame(animationRef.current);
    if(streamRef.current) streamRef.current.getTracks().forEach(t=>t.stop());
    if(audioCtxRef.current) audioCtxRef.current.close();
  }

  return {canvasRef,error};
}
