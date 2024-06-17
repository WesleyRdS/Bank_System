document.addEventListener("DOMContentLoaded", 
    function(){
        //block to verify a type of account
        var identifier = document.getElementsByName("identifier");
        var CPF = document.getElementById("cpf_field");
        var CNPJ = document.getElementById("cnpj_field");

        //joint account blocks 
        var label_type_account = document.getElementById("label_type_account");
        var ADD_cpf_forms_dynamic = document.getElementById("cpf_forms_dynamic");
        var add_cpf = document.getElementById("add_cpf");
        var cpf_index = 1;
        var type_account = document.getElementsByName("type_account");
        var add_cpf_button = document.getElementById("add_cpf_button");
        
        //block to add cpf number dynamically
        add_cpf.addEventListener("click", function(){
                var new_cpf_div = document.createElement("div");
                new_cpf_div.classList.add("form-group");

                var new_cpf_label = document.createElement("label");
                new_cpf_label.textContent = "CPF-Joint(" + cpf_index + "):";

                var new_cpf_input = document.createElement("input");
                new_cpf_input.type = "text";
                new_cpf_input.name = "cpf" + cpf_index;
                new_cpf_input.placeholder = "000.000.000-00";
                new_cpf_input.required = true;

                new_cpf_div.appendChild(new_cpf_label);
                new_cpf_div.appendChild(new_cpf_input);

                ADD_cpf_forms_dynamic.appendChild(new_cpf_div);

                cpf_index++;
            }
        );
      

        //verify field in exibition
        function to_hide_field(){
            if(identifier[0].checked){
                CPF.style.display = 'block';
                CNPJ.style.display = 'none';
                label_type_account.style.display = 'block';
            }
            else if(identifier[1].checked){
                CPF.style.display = 'none';
                CNPJ.style.display = 'block';
                label_type_account.style.display = 'none';
            }
        }

        function to_hide_botton(){
            if(type_account[0].checked){
                add_cpf_button.style.display = 'none';
            }
            else if(type_account[1].checked){
                add_cpf_button.style.display = 'block';
            }
        }

        
        for(var itarator = 0; itarator < identifier.length; itarator++){
            identifier[itarator].addEventListener('change', to_hide_field);
            type_account[itarator].addEventListener('change', to_hide_botton);
        }


        to_hide_field();
        to_hide_botton();
    }
);