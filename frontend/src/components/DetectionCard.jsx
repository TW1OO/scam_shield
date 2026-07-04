import React from "react";
export default function DetectionCard({title,desc,badge}){return <div className="bio-row"><div><div>{title}</div><div>{desc}</div></div><span>{badge}</span></div>}