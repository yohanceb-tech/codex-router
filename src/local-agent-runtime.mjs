// Evidence-based capability hints; no tool injection, execution, or permission changes.
export function localRuntimeToolContext(tools) {
 const names=[];
 const walk=(rows,prefix='')=>{for(const t of Array.isArray(rows)?rows:[]){
  if(t?.type==='namespace' && typeof t.name==='string' && /^[a-zA-Z0-9_.:-]+$/.test(t.name))walk(t.tools,prefix+t.name+'__');
  else if(t?.type==='tool_search')names.push('tool_search');
  else if(typeof t?.name==='string' && /^[a-zA-Z0-9_.:-]+$/.test(t.name))names.push(prefix+t.name);
 }};walk(tools);
 const categories=[['Chat lookup',/(?:^|__)list_threads$|(?:^|__)read_thread$/],['Browser and desktop',/cua_repl.*__js$/],['Project context',/search_project_context$/],['File edits',/read_project_file$|write_project_file$|apply_patch$/],['Verification',/run_project_check$|exec_command$|shell_command$/],['Tool discovery',/tool_search$|search_tools$/]];
 const lines=categories.map(([label,pattern])=>label+': '+(names.filter(n=>pattern.test(n)).slice(0,6).join(', ')||'not declared in this turn'));
 return '## Actual tool context for this turn\n'+lines.join('\n')+'\nThese names come from the current tool declarations. Use their actual schemas and permissions. A declared tool permits an attempt within user authorization; it does not prove login/access or success. If a needed tool is not declared, use an offered discovery tool or report that specific limitation. For an authorized action, make a real tool call; do not print call JSON as your answer. Prefer run_project_check when declared; after a project read/search, omit its root to reuse the validated directory. Run relevant verification before claiming completion. Never send messages or publish without the required user authorization.';
}
export function applyLocalRuntimeToolContext(payload,route) {
 if(route?.slug!=='local/gpt-oss:20b')return payload;
 const hint=localRuntimeToolContext(payload.tools);
 return {...payload,instructions:(typeof payload.instructions==='string'?payload.instructions+'\n\n':'')+hint};
}
