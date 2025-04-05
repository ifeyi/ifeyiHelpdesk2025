let helpdeskSvgEyeOn = document.getElementById("helpdesk-svg-eye-on");
let helpdeskSvgEyeOff = document.getElementById("helpdesk-svg-eye-off");
let helpdeskPassword = document.getElementById("password");

if(helpdeskPassword){
    helpdeskPassword.addEventListener("input", () => {
        if(helpdeskPassword.value.length > 0){
            helpdeskSvgEyeOn.addEventListener("click", () => {
                helpdeskSvgEyeOn.classList.add("helpdesk-none");
                helpdeskSvgEyeOff.classList.remove("helpdesk-none");
                helpdeskPassword.type = "text";
            });
            helpdeskSvgEyeOff.addEventListener("click", () => {
                helpdeskSvgEyeOff.classList.add("helpdesk-none");
                helpdeskSvgEyeOn.classList.remove("helpdesk-none");
                helpdeskPassword.type = "password";
            });
        }
    });
}