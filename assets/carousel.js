// Adds the header and footer to every slide so each post file only holds content.
const s=[...document.querySelectorAll('.slide')],m=document.body.dataset;
s.forEach((el,i)=>{
 const n=String(i+1).padStart(2,'0')+' / '+String(s.length).padStart(2,'0');
 el.insertAdjacentHTML('afterbegin',`<div class="hd"><span>${m.series} · Day ${m.day}</span><span class="n">${n}</span></div>`);
 const last=i===s.length-1, final=+m.day>=+m.total;
 el.insertAdjacentHTML('beforeend',`<div class="ft"><span><b>${m.author}</b><i>${m.role}</i></span><span class="sw">${last?(final?'Follow for more':'Follow for Day '+(+m.day+1)):'Swipe →'}</span></div>`);
});
// Layout self-check used by build/build.py (open the page with #check).
if(location.hash==='#check'){
 const bad=[];
 s.forEach((el,i)=>{
  const r=el.getBoundingClientRect(),hd=el.querySelector('.hd').getBoundingClientRect(),tag=el.querySelector('.tag').getBoundingClientRect(),ft=el.querySelector('.ft'),f=ft.getBoundingClientRect(),prev=ft.previousElementSibling.getBoundingClientRect();
  if(f.bottom>r.bottom-40) bad.push('s'+(i+1)+':overflow');
  else if(tag.top-hd.bottom<24||f.top-prev.bottom<10) bad.push('s'+(i+1)+':tight');
 });
 document.title=bad.length?bad.join(' '):'OK';
}
