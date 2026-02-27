const menuBtn=document.getElementById('menuBtn');
const mobileNav=document.getElementById('mobileNav');
if(menuBtn&&mobileNav){menuBtn.addEventListener('click',()=>mobileNav.classList.toggle('hidden'));}
const io=new IntersectionObserver((entries)=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')}),{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));