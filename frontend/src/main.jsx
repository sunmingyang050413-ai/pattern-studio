import React, {useEffect, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {api} from './api';
import './style.css';

const active = job => job && ['QUEUED', 'RUNNING'].includes(job.status);
const modes = [{id: 'replace', title: 'Find & replace', description: 'Mask or replace a pattern', icon: '↔'}, {id: 'extract', title: 'Extract a value', description: 'Keep matches in new columns', icon: '↗'}, {id: 'normalize', title: 'Clean up text', description: 'Standardize case & spacing', icon: '≋'}];
const examples = {replace: 'Find email addresses and replace them with the replacement value.', extract: 'Extract the first email address from each cell.', normalize: 'Trim the text, collapse repeated spaces, and convert to lowercase.'};

export function App() {
  const [connection, setConnection] = useState(null);
  const [files, setFiles] = useState([]), [cursor, setCursor] = useState('');
  const [prefix, setPrefix] = useState(''), [selected, setSelected] = useState('');
  const [source, setSource] = useState(null), [columns, setColumns] = useState([]);
  const [mode, setMode] = useState('replace'), [prompt, setPrompt] = useState(''), [replacement, setReplacement] = useState('REDACTED');
  const [job, setJob] = useState(null), [history, setHistory] = useState([]);
  const [resultId, setResultId] = useState(null), [result, setResult] = useState(null), [page, setPage] = useState(1);
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [loadingPage, setLoadingPage] = useState(false);
  const handled = useRef(null);
  const running = active(job), locked = running || busy;

  useEffect(() => {
    Promise.all([api('session/'), api('jobs/')]).then(([session, data]) => {
      setHistory(data.jobs);
      const restored = session.connections[0];
      if (restored) {
        setConnection(restored);
        const previous = data.jobs.find(j => j.connection_id === restored.id && j.kind === 'inspect' && j.status === 'SUCCESS');
        if (previous) setSource(previous);
        const latest = data.jobs.find(j => j.connection_id === restored.id && (active(j) || j.status === 'SUCCESS'));
        if (latest) setJob(latest);
      }
    }).catch(e => setError(e.message));
  }, []);
  useEffect(() => {
    if (!job?.id || !active(job)) return;
    let stopped = false, timer;
    const poll = async () => {
      try {
        const next = await api(`jobs/${job.id}/`);
        if (!stopped) {setJob(next); setError('');}
      } catch (e) {if (!stopped) setError('Status connection interrupted. Reconnecting… ' + e.message);}
      if (!stopped) timer = setTimeout(poll, 1500);
    };
    timer = setTimeout(poll, 500);
    return () => {stopped = true; clearTimeout(timer);};
  }, [job?.id, job?.status]);

  useEffect(() => {
    if (!job || active(job) || handled.current === job.id) return;
    handled.current = job.id;
    api('jobs/').then(data => setHistory(data.jobs)).catch(() => {});
    if (job.status === 'FAILED') {setError(job.error); return;}
    if (job.status !== 'SUCCESS') return;
    if (job.kind === 'list') {setFiles(job.output.files); setCursor(job.output.cursor);}
    else {
      setResultId(job.id); setPage(1);
      if (job.kind === 'inspect') {setSource(job); setColumns([]);}
    }
  }, [job]);

  useEffect(() => {
    if (!resultId) return;
    let stopped = false;
    setLoadingPage(true);
    api(`jobs/${resultId}/result/?page=${page}&page_size=25`).then(data => {if (!stopped) setResult(data);})
      .catch(e => {if (!stopped) setError(e.message);}).finally(() => {if (!stopped) setLoadingPage(false);});
    return () => {stopped = true;};
  }, [resultId, page]);

  async function action(callback) {
    setBusy(true); setError('');
    try {await callback();} catch (e) {setError(e.message);} finally {setBusy(false);}
  }
  function watch(id, kind) {handled.current = null; setJob({id, kind, status: 'QUEUED', progress: 0, stage: 'Waiting for a worker', output: {}});}
  async function connect(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = Object.fromEntries(new FormData(form));
    await action(async () => {
      const response = await api('connections/', data);
      setConnection({id: response.connection_id, bucket: data.bucket});
      form.reset(); setFiles([]); setCursor(''); setSource(null); setResult(null); setResultId(null);
      watch(response.job_id, 'list');
    });
  }
  async function submit(kind, extra = {}) {
    await action(async () => {
      const response = await api('jobs/submit/', {connection_id: connection.id, kind, ...extra});
      watch(response.job_id, kind);
    });
  }
  const pages = Math.max(1, Math.ceil((result?.total || 0) / 25));

  return <div className="shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="Pattern Studio home"><span className="brand-mark">◇</span><span>pattern<span className="brand-light">studio</span></span></a>
      <div className="workspace-label">YOUR WORKSPACE</div>
      <div className="nav-item"><span>▦</span> Data workbench <span className="nav-dot"/></div>
      <div className="sidebar-section"><div className="workspace-label">RECENT JOBS</div>
        {history.length === 0 ? <p className="sidebar-empty">Your processing history will appear here.</p> : history.slice(0, 8).map(item => <button className="history-item" disabled={locked} key={item.id} onClick={() => {handled.current = null; setJob(item);}}><span className={`status-dot ${item.status.toLowerCase()}`}/><span>{item.kind === 'transform' ? 'Transformation' : item.kind === 'inspect' ? 'File preview' : 'S3 connection'}<small>{item.status.toLowerCase()} · {new Date(item.created_at).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</small></span></button>)}
      </div>
      <div className="sidebar-bottom"><span className="avatar">M</span><div>My workspace<small>Rhombus AI take-home</small></div></div>
    </aside>
    <main>
      <header className="topbar"><span>Workspace <span className="slash">/</span> <strong>Data workbench</strong></span><span className="top-tag">Django + React · Spark powered</span></header>
      <div className="content">
        <div className="heading"><div><div className="eyebrow">LESS MANUAL CLEANUP. MORE CLARITY.</div><h1>Good data starts here.</h1><p>Describe what to change. Let your data do the rest.</p></div><span className="private-badge"><span>◈</span> Private session</span></div>
        <div className="steps"><div className="step current"><b>1</b><span>Connect your data</span></div><span className="step-line"/><div className={`step ${source ? 'current' : ''}`}><b>2</b><span>Describe a change</span></div><span className="step-line"/><div className={`step ${result ? 'current' : ''}`}><b>3</b><span>Explore the result</span></div></div>
        {error && <div className="alert" role="alert"><span>{error}</span><button aria-label="Dismiss error" onClick={() => setError('')}>×</button></div>}
        <div className="work-grid">
          <section className="card source-card"><div className="card-heading"><span className="section-icon">▱</span><div><h2>Your data source</h2><p>Connect directly to Amazon S3.</p></div>{connection && <span className="pill">Connected session</span>}</div>
            {!connection ? <form onSubmit={connect} className="form-stack">
              <label>Bucket name<input required name="bucket" placeholder="my-data-bucket" autoComplete="off" maxLength={63}/></label>
              <label>AWS region<input required name="region" defaultValue="us-east-1" placeholder="us-east-1"/></label>
              <label>Access key ID<input required name="access_key" type="password" autoComplete="off" placeholder="AWS access key ID" minLength={16}/></label>
              <label>Secret access key<input required name="secret_key" type="password" autoComplete="new-password" placeholder="AWS secret access key" minLength={16}/></label>
              <details><summary>Temporary credentials?</summary><label>Session token<textarea name="session_token" rows={2} autoComplete="off" placeholder="Optional AWS session token"/></label></details>
              <button className="primary" disabled={locked}>{busy ? 'Connecting…' : 'Connect to S3'} <span>→</span></button>
              <p className="privacy-note">◈ Credentials are encrypted, never sent to the LLM, and expire after 24 hours.</p>
            </form> : <div className="form-stack">
              <div className="bucket"><span>▱</span><div><strong>{connection.bucket}</strong><small>Amazon S3 · CSV / XLSX / XLS</small></div></div>
              <form onSubmit={e => {e.preventDefault(); setSelected(''); submit('list', {prefix});}}><label>Folder prefix<div className="inline"><input value={prefix} onChange={e => setPrefix(e.target.value)} placeholder="Optional: exports/"/><button className="secondary" disabled={locked}>Browse</button></div></label></form>
              <label>Choose a file<select value={selected} onChange={e => setSelected(e.target.value)} disabled={locked}><option value="">Select a file…</option>{files.map(file => <option key={file.key} value={file.key}>{file.key} ({(file.size / 1024).toFixed(1)} KB)</option>)}</select></label>
              {!files.length && !running && <p className="hint">No supported files on this S3 page. Try a prefix or the next page.</p>}
              {cursor && <button className="text-button" disabled={locked} onClick={() => {setSelected(''); submit('list', {cursor, prefix});}}>Next S3 file page →</button>}
              <button className="primary" disabled={locked || !selected} onClick={() => {setSource(null); setColumns([]); submit('inspect', {key: selected});}}>Load & preview file <span>→</span></button>
              <button className="text-button" disabled={locked} onClick={() => action(async () => {await api(`connections/${connection.id}/disconnect/`, {}); setConnection(null); setSource(null); setFiles([]); setResult(null); setResultId(null); setJob(null); setHistory([]);})}>Disconnect & delete session data</button>
            </div>}
          </section>
          <section className="card transform-card"><div className="card-heading"><span className="section-icon">✧</span><div><h2>Make a transformation</h2><p>A little language. A powerful change.</p></div></div>
            <div className="mode-tabs" role="group" aria-label="Transformation type">{modes.map(item => <button className={`mode ${mode === item.id ? 'selected' : ''}`} key={item.id} disabled={locked} aria-pressed={mode === item.id} onClick={() => {setMode(item.id); setPrompt('');}}><span>{item.icon}</span><strong>{item.title}</strong><small>{item.description}</small></button>)}</div>
            <div className="form-stack"><label>What would you like to do?<textarea value={prompt} onChange={e => setPrompt(e.target.value)} maxLength={2000} rows={3} placeholder={examples[mode]} disabled={locked}/></label><button className="example-button" disabled={locked} onClick={() => setPrompt(examples[mode])}>↳ Try an example</button>
              <div className="transform-fields"><fieldset><legend>Target columns</legend>{source ? <div className="column-list">{source.output.columns.map(column => <label className="checkbox" key={column}><input type="checkbox" checked={columns.includes(column)} disabled={locked} onChange={e => setColumns(e.target.checked ? [...columns, column] : columns.filter(x => x !== column))}/>{column}</label>)}</div> : <div className="disabled-field">Load a file to select columns</div>}</fieldset>{mode === 'replace' && <label>Replace with<input value={replacement} onChange={e => setReplacement(e.target.value)} maxLength={1000} disabled={locked} placeholder="Leave blank to remove matches"/></label>}</div>
              <div className="transform-footer"><span className="hint">{mode === 'extract' ? 'Creates a new “_extracted” column.' : 'Your original S3 file stays unchanged.'}</span><button className="primary" disabled={locked || !source || !columns.length || !prompt.trim()} onClick={() => submit('transform', {source_id: source.id, mode, prompt, replacement, columns})}>Run transformation <span>↗</span></button></div>
            </div>
          </section>
        </div>
        {job && <section className="job-card" aria-live="polite"><div className="job-status"><span className={`status-dot ${job.status.toLowerCase()}`}/><strong>{job.stage}</strong><span className="pill">{job.status}</span>{running && <button className="text-button cancel" onClick={() => action(async () => setJob(await api(`jobs/${job.id}/cancel/`, {})))}>Cancel job</button>}</div><div className="progress" role="progressbar" aria-label="Job progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={job.progress}><span style={{width: `${job.progress}%`}}/></div><div className="job-meta"><span>{job.id}</span><span>{job.progress}% · stage-based progress</span></div>{job.output?.plan && <div className="plan"><strong>Transformation plan</strong><code>{job.output.plan.pattern || job.output.plan.operations.join(' → ')}</code><p>{job.output.plan.explanation} {job.output.cache_hit && <span className="pill">Cached plan</span>}</p></div>}</section>}
        <section className="card results"><div className="result-heading"><div><h2>{source?.id === resultId ? 'Source preview' : 'Data preview'}</h2><p>{result ? `${result.total.toLocaleString()} rows · ${result.columns.length} columns` : 'Your data, with a fresh perspective.'}</p></div>{result && <span className="pill">{loadingPage ? 'Loading…' : 'Ready to explore'}</span>}</div>
          {!result ? <div className="empty-state"><div className="empty-icon">▤</div><h3>A clearer view is on its way.</h3><p>Connect a bucket and load a file to preview your data here.</p><span>CSV & Excel supported · Paginated results</span></div> : <><div className="table-scroll" aria-busy={loadingPage}><table><thead><tr>{result.columns.map(column => <th key={column}>{column}</th>)}</tr></thead><tbody>{result.rows.map((row, i) => <tr key={i}>{row.map((cell, c) => <td key={c}>{cell === null ? <span className="null">null</span> : cell}</td>)}</tr>)}</tbody></table>{!result.rows.length && <p className="empty-table">No rows to display. This file may contain only headers.</p>}</div><div className="pagination"><span>Page {result.page} of {pages} <span className="slash">·</span> 25 rows per page</span><div><button className="secondary" disabled={loadingPage || page <= 1} onClick={() => setPage(x => x - 1)}>← Previous</button><button className="secondary" disabled={loadingPage || page >= pages} onClick={() => setPage(x => x + 1)}>Next →</button></div></div></>}
        </section>
        <footer>Built for thoughtful data work.<span>Asynchronous processing · Distributed transformations</span></footer>
      </div>
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App/>);
