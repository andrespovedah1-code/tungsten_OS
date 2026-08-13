(function(){
  const header=document.querySelector('.site-header');
  const syncHeader=()=>header&&header.classList.toggle('is-scrolled',window.scrollY>10);
  syncHeader(); addEventListener('scroll',syncHeader,{passive:true});
  const nodes=[...document.querySelectorAll('[data-reveal]')];
  if(!('IntersectionObserver' in window)){nodes.forEach(n=>n.classList.add('is-visible'));return;}
  const io=new IntersectionObserver((entries)=>{entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('is-visible');io.unobserve(entry.target);}})},{threshold:.12,rootMargin:'0px 0px -5% 0px'});
  nodes.forEach(n=>io.observe(n));
})();
