document.addEventListener("DOMContentLoaded", 
    function(){
        //block to verify a type of account
        var identifier = document.getElementsByName("identifier");
        var CPF = document.getElementById("cpf_field");
        var CNPJ = document.getElementById("cnpj_field");
        //texts fields required change
        function change_required(op, id){
            const inputElement = document.getElementById(id);
            if(op == true){
                inputElement.required = op;
            }else{
                inputElement.required = op;
            }
        }

         //verify field in exibition
        function to_hide_field(){
            if(identifier[0].checked){
                CPF.style.display = 'block';
                CNPJ.style.display = 'none';
                change_required(true, "cpf");
                change_required(false, "cnpj");

            }
            else if(identifier[1].checked){
                CPF.style.display = 'none';
                CNPJ.style.display = 'block';
                change_required(false, "cpf");
                change_required(true, "cnpj");

            }
        }

        for(var itarator = 0; itarator < identifier.length; itarator++){
            identifier[itarator].addEventListener('change', to_hide_field);
        }


        to_hide_field();
    }
);