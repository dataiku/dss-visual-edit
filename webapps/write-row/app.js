// Access the parameters that end-users filled in using webapp config
// For example, for a parameter called "input_dataset"
// input_dataset = dataiku.getWebAppConfig()['input_dataset']



var validator = undefined
var columns = undefined
$.getJSON(getWebAppBackendUrl('get_dataset_schema'),
          function(data){
          columns = data['columns']
          var validation_rules = {};
          var validation_messages = {}
          $.each(columns, function(index, value){
              
              console.log(value['name'], value['type'])
              var name = value['name'];
              var type = value['type'];
              
              /*
              Construction du formulaire à partir du JSON renvoyé par le backend Python.
              Il y a des conditions qui correspondent à chaque type de variable
              */
              if (type == 'string'){ var input =`<input class="form-control" id="${name}" placeholder="value for ${name}" data-rule-minlength="1">`}
              else if (type =='double'){var input =`<input class="form-control" id="${name}" placeholder="value for ${name}" data-rule-number="true">`}
              else if (type == 'bigint'){var input =`<input class="form-control" id="${name}" placeholder="value for ${name}" data-rule-digits="true">`}
              
              else if (type == 'date') { var input = `<div class='input-group date' id='datetimepicker1'>
                                                        <input type='text' class="form-control" id="${name}" />
                                                        <span class="input-group-addon">
                                                        <span class="glyphicon glyphicon-calendar"></span>
                                                        </span>
                                                      </div>`}
              else if (type == 'boolean') {
                  var input = `<input type="checkbox" class="form-check-input form-control" id="${name}">`
              }
              
              else if ((type == 'categorical') && (typeof value['parent'] === 'undefined')){
                  
                  var uniques= value['uniques']
                  var input =`<select class="custom-select form-control" id="${name}"><option hidden disabled selected value> select an option </option>`
                  $.each(uniques, function(id,val){
                      input = input + `<option value="${val}">${val}</option>`
                      
                  });
                  
                  
                  
                  var input = input + `</option>`
              }
              
              else if ((type == 'categorical') && (typeof value['parent'] !== 'undefined')){
                  var input= `<select class="custom-select form-control" id="${name}" disabled ></select>`
              }
              
   

              $('.fg').append(`
                                <div class="col-sm-6 table-field">
                                <div class="row">
                                <label for="${name}" class="col-sm-4 col-form-label">${name} <span style="font-size:10px; color:#7f8c8d"> (${type})</span></label>
                                <div class="col-sm-5 form-element">
                                  ${input}
                                </div>
                                </div>
                                </div>
                              `);
              
             /*
             Gestion des champs interdépendants :
             Si un champ est identifié comme ayant un child : 
             lorsqu'une valeur est sélectionnée pour ce champ, on va récupérer les valeurs correspondantes pour l'élément enfant et on les ajoute à la liste déroulante 
              */
             if ((type == 'categorical') && (typeof value['parent'] === 'undefined')) {$('#'+name).on('change', function(){
                      
                      var el = $.grep(columns, function(v) {
                            return v.name === name 
                        });
                      var el_dict = el[0];
                      var params = {}
                      params['child'] = el_dict['child']
                      params['selected'] = $(this).find("option:selected").val()
                      params['parent'] = name
                      $.getJSON(getWebAppBackendUrl('get_dropdown_values')+'/'+JSON.stringify(params), function(data){
                          $('#'+params['child']).empty();
                          $.each(data['data'], function(i, v){
                              $('#'+params['child']).append(`<option value="${v}">${v}</option>`)
                          });
                         $('#'+params['child']).prop('disabled',false)
                          
                      })
                  });}
              
              
              
          });
    $('#datetimepicker1').datetimepicker({
        format:'YYYY-MM-DD HH:mm:ss'
    });
    
    /*
      Règles de validation         
     */
    validator = $("#to_validate").validate({
        //messages: validation_messages,
        errorElement: "em",
				errorPlacement: function ( error, element ) {
					// Add the `help-block` class to the error element
					error.addClass( "help-block" );

					// Add `has-feedback` class to the parent div.form-group
					// in order to add icons to inputs
					element.parents( ".col-sm-5" ).addClass( "has-feedback" );

					if ( element.prop( "type" ) === "checkbox" ) {
						error.insertAfter( element.parent( "label" ) );
					} else {
						error.insertAfter( element );
					}

					// Add the span element, if doesn't exists, and apply the icon classes to it.
					if ( !element.next( "span" )[ 0 ] ) {
						$( "<span class='glyphicon glyphicon-remove form-control-feedback'></span>" ).insertAfter( element );
					}
				},
				success: function ( label, element ) {
					// Add the span element, if doesn't exists, and apply the icon classes to it.
					if ( !$( element ).next( "span" )[ 0 ] ) {
						$( "<span class='glyphicon glyphicon-ok form-control-feedback'></span>" ).insertAfter( $( element ) );
					}
				},
				highlight: function ( element, errorClass, validClass ) {
					$( element ).parents( ".form-element" ).addClass( "has-error" ).removeClass( "has-success" );
					$( element ).next( "span" ).addClass( "glyphicon-remove" ).removeClass( "glyphicon-ok" );
				},
				unhighlight: function ( element, errorClass, validClass ) {
					$( element ).parents( ".form-element" ).addClass( "has-success" ).removeClass( "has-error" );
					$( element ).next( "span" ).addClass( "glyphicon-ok" ).removeClass( "glyphicon-remove" );
				}
        
    });
})

/*
    Interaction lors du clic sur le bouton, envoi d'un call d'API au backend pour écriture dans la table          
*/
$('#write').on('click', function(){
    var data = {}
    console.log(validator.numberOfInvalids())
    validator.showErrors()
    $('.form-control').each(function(index,value){
        console.log(value.id)
        if($('#'+value.id).val()=="on"){
            data[value.id] = $('#'+value.id).is(':checked')
        }
        else {
            data[value.id] = $('#'+value.id).val()
        }
    });
    console.log(data)
    $.post(getWebAppBackendUrl('write_row'),JSON.stringify({'row': data}),function(data){
        var data1 = jQuery.parseJSON(data)
        console.log(jQuery.type(data1))
        console.log(Object.keys(data1))
        console.log(data1.status)
        if (data1.status=='ok'){
            console.log('ok')
            $('#success').show()
        }
        else {
            $('#error').show()
        }
    })
})






   
