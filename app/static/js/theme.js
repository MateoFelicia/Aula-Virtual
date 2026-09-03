
if(!tema_guardado){
    tema_guardado = 'light'
    localStorage.setItem('tema', 'light')
}
document.documentElement.dataset.theme = tema_guardado

const switch_tema = document.getElementById('theme-toggle')

if (tema_guardado == 'dark'){
        switch_tema.textContent = "☀️"
    } else {
        switch_tema.textContent = "🌙"
    }

switch_tema.addEventListener("click", ()=>{
    let tema_actual = document.documentElement.dataset.theme
    if (tema_actual == 'dark'){
        document.documentElement.dataset.theme = 'light'
        switch_tema.textContent = "🌙"
        localStorage.setItem('tema','light')
    } else {
        document.documentElement.dataset.theme = 'dark'
        switch_tema.textContent = "☀️"
        localStorage.setItem('tema','dark')
    }
})
