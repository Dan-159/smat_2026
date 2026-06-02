import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'login_screen.dart';
class AddEstacionScreen extends StatefulWidget {
  const AddEstacionScreen({super.key});

  @override
  State<AddEstacionScreen> createState() => _AddEstacionScreenState();
}

class _AddEstacionScreenState extends State<AddEstacionScreen> {
  final _formKey = GlobalKey<FormState>();
  final _idController = TextEditingController();
  final _nombreController = TextEditingController();
  final _ubicacionController = TextEditingController();
  final ApiService _apiService = ApiService();

  //-----------
  @override
  void dispose() {
    _idController.dispose();
    _nombreController.dispose();
    _ubicacionController.dispose();
    super.dispose();
  }

  void _guardar() async {
    if (_formKey.currentState!.validate()) {
      final int? idAsInt = int.tryParse(_idController.text);
      if (idAsInt == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('El ID debe ser un número válido')),
        );
        return;
      }

      try {
        bool success = await _apiService.crearEstacion(
          idAsInt,
          _nombreController.text,
          _ubicacionController.text,
        );

        if (!mounted) return;

        if (success) {
          Navigator.pop(context, true);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Error: Servidor caído o inválido')),
          );
        }
      } on UnauthorizedException {
        if (!mounted) return;
        // Redirigir limpiando el historial si el token expiró
        Navigator.pushAndRemoveUntil(
          context,
          MaterialPageRoute(builder: (context) => const LoginScreen()),
          (route) => false,
        );
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Sesión expirada. Inicie sesión de nuevo.'),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Nueva Estación')),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          // Evita errores de overflow si se abre el teclado
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              TextFormField(
                controller: _idController,
                decoration: const InputDecoration(labelText: 'ID (Número)'),
                keyboardType: TextInputType.number, // Abre teclado numérico
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              TextFormField(
                controller: _nombreController,
                decoration: const InputDecoration(labelText: 'Nombre'),
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              TextFormField(
                controller: _ubicacionController,
                decoration: const InputDecoration(labelText: 'Ubicación'),
                validator: (v) => v!.isEmpty ? 'Requerido' : null,
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: _guardar,
                child: const Text('Guardar Estación'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}