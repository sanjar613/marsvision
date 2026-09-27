import { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';

export default function FileUploadZone({ onUpload, disabled }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const submitFile = (file) => {
    if (!disabled && file) onUpload(file);
    setDragActive(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    if (!disabled) submitFile(event.dataTransfer.files?.[0]);
  };

  const handleKeyDown = (event) => {
    if (disabled || !['Enter', ' '].includes(event.key)) return;
    event.preventDefault();
    inputRef.current?.click();
  };

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label="Choose or drop a traffic video"
      aria-disabled={disabled}
      onClick={() => { if (!disabled) inputRef.current?.click(); }}
      onKeyDown={handleKeyDown}
      onDragEnter={(event) => { event.preventDefault(); if (!disabled) setDragActive(true); }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setDragActive(false); }}
      onDrop={handleDrop}
      className={`file-upload-zone${dragActive ? ' is-active' : ''}`}
    >
      <span className="upload-icon"><UploadCloud size={25} /></span>
      <span className="upload-title">Drop a traffic video here</span>
      <span className="upload-formats">or click to browse <b>MP4</b><b>AVI</b><b>MOV</b></span>
      <span className="upload-destination">SENT TO CONFIGURED API</span>
      <input
        ref={inputRef}
        type="file"
        accept=".mp4,.avi,.mov,video/mp4,video/x-msvideo,video/quicktime"
        aria-hidden="true"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
        onChange={(event) => {
          submitFile(event.currentTarget.files?.[0]);
          event.currentTarget.value = '';
        }}
        disabled={disabled}
        style={{ display: 'none' }}
      />
    </div>
  );
}