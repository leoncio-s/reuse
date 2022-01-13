function checkInput(fields){
    var check = true;

    fields.forEach( field => {
        if ((field.name=='user' || field.name=='email') && (field.value.match(/^[^\w.-]+|[^\w@.-]+/)) != null){
            console.log(field.value.match(/[^\W.-]|[^\W@.-]+/));
            field.focus();
            field.setCustomValidity("Caracteres inválidos")
        }
        else{
            field.setCustomValidity('')
        }
        
        if ((field.name=='username' ) && (field.value.match(/[^A-Za-z0-9_-]/)) != null){
            field.focus();
            field.setCustomValidity("Caracteres inválidos")
        }
        else{
            field.setCustomValidity('')
        }
        if ((field.name == 'password' || field.name=='confirmpassword') && (field.value.match(/[^a-zA-Z0-9+.?!@#/$%&_-]+/) != null)){
            field.focus()
            field.setCustomValidity("Caracteres inválidos")
        }
        else{
            field.setCustomValidity('')
        }
        if(field.value.match(/\s\W[^A-Za-z ]+/) != null){
            field.focus()
            field.setCustomValidity("Caracteres inválidos")
        }else{
            field.setCustomValidity('')
        }

        if(field.name == 'user' || field.name=="email"){field.value = field.value.toLowerCase()}


        if(field.validity.valid === false && field.value.length < 5){
            check = false
        }  
    });

    return check;
}

var inputs = document.querySelectorAll("form input")
var button = $("form button")

inputs.forEach( field =>{
    field.addEventListener("keyup", (e)=>{
        //console.log(e);
        if(checkInput(inputs)){
            button.removeClass("disabled")
        }else{
            button.addClass("disabled")
        }
    })
})

$("form").on("submit", ()=>{

        $(".progress").removeClass("hide");
    
})
