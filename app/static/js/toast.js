document.querySelectorAll('#toast-container .toast').forEach(toast =>{
            setTimeout(() => {
                toast.classList.add('hide');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        });