# Video-Tagger
A desktop video annotation tool that enables users to load local videos, inspect frames, and assign tags for labeling, analysis, or dataset creation.



## TODO:
 -- Agregar una ventana principal al inicio que permita seleccionar la carpeta donde se encuentran los fragmentos de video ha etiquetar, para que esta carpeta se agregue al menú principal
 -- Agregar una vista de proyectos recientes (vista general con iconos de carpetas)
 -- Agregar la opcion de actualizar el proyecto en lugar de volver a guardarlo
 -- Revisar que el proyecto se guarde aunque no se presione el botón de "Guardar Proyecto"
 -- Agregar un botón para regresar al fragmento anterior, eliminar la etiqueta actual y cambiar la disposicion y tamaño de los botones 
-- Guardar el proyecto una vez que se ejecuta el metodo _on_back(), cuando se sale de la aplicación o mandar el mensaje al usuario de que si desea guardar los cambios
-- Habilitar los botones de siguiente/anterior una vez que se guardo la etiqueta del fragmento
-- Cambiar la logica actual para que los detalles (Estatus) se actualice una vez que se presiona el boton de "Guardar y continuar", o al entrar a la vista, que solo se actualice el panel de la etiqueta cuando se selecciona una de estas.
-- Agregar actualización de archivos sincronizada con el proyecto (progreso parcial)
-- Agregar una funcionalidad que revise el estatus del proyecto cuando se reanuda (volver a cargar el estado del proyecto)