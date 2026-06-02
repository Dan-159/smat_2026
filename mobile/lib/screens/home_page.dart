import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/api_service.dart';
import '../models/estacion.dart';
import 'login_screen.dart';
import 'add_estacion.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final ApiService apiService = ApiService();
  late Future<List<Estacion>> futureEstaciones;

  @override
  void initState() {
    super.initState();
    _cargarEstaciones();
  }

  void _cargarEstaciones() {
    setState(() {
      futureEstaciones = apiService.obtenerEstaciones();
    });
  }

  void _mostrarDialogoEdicion(Estacion estacion) {
    final nombreCtrl = TextEditingController(text: estacion.nombre);
    final ubicacionCtrl = TextEditingController(text: estacion.ubicacion);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Editar Estación"),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nombreCtrl,
              decoration: const InputDecoration(labelText: "Nombre"),
            ),
            TextField(
              controller: ubicacionCtrl,
              decoration: const InputDecoration(labelText: "Ubicación"),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              nombreCtrl.dispose();
              ubicacionCtrl.dispose();
              Navigator.pop(context);
            },
            child: const Text("Cancelar"),
          ),
          TextButton(
            onPressed: () async {
              try {
                bool ok = await apiService.editarEstacion(
                  estacion.id,
                  nombreCtrl.text,
                  ubicacionCtrl.text,
                );

                if (!context.mounted) return;

                if (ok) {
                  Navigator.pop(context);
                  _cargarEstaciones();
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text("Estación modificada con éxito"),
                    ),
                  );
                } else {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text("Error al modificar la estación"),
                    ),
                  );
                }
              } on UnauthorizedException {
                Navigator.pop(context); 
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
              }catch (_) {
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Error de conexión. ¿Está el servidor activo?'),
                  ),
                );
              }
            },
            child: const Text("Guardar"),
          ),
        ],
      ),
    );
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Estaciones SMAT'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () async {
              await AuthService().logout();
              if (!mounted) return;
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => const LoginScreen()),
                (route) => false,
              );
            },
          ),
        ],
      ),
      body: FutureBuilder<List<Estacion>>(
        future: futureEstaciones,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } 
          else if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('${snapshot.error}', textAlign: TextAlign.center),
                  const SizedBox(height: 10),
                  ElevatedButton(
                    onPressed: _cargarEstaciones,
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          } 
          else if (!snapshot.hasData || snapshot.data!.isEmpty) {
            return const Center(child: Text('No hay estaciones disponibles'));
          }
          final estaciones = snapshot.data!;

          return RefreshIndicator(
            onRefresh: () async {
              _cargarEstaciones();
              await futureEstaciones;
            },
            child: ListView.builder(
              itemCount: estaciones.length,
              itemBuilder: (context, index) {
                final estacion = estaciones[index];

                return Dismissible(
                  key: Key(estacion.id.toString()),
                  direction: DismissDirection
                      .endToStart, // Deslizar de derecha a izquierda
                  background: Container(
                    color: Colors.red,
                    alignment: Alignment.centerRight,
                    padding: const EdgeInsets.only(right: 20),
                    child: const Icon(Icons.delete, color: Colors.white),
                  ),

                  confirmDismiss: (direction) async {
                    try {
                      bool eliminadoExitoso = await apiService.eliminarEstacion(
                        estacion.id,
                      );

                      if (eliminadoExitoso) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: Text(
                              "${estacion.nombre} eliminada correctamente",
                            ),
                          ),
                        );
                        return true;
                      } else {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text("Error al eliminar la estación"),
                          ),
                        );
                        return false;
                      }
                    } on UnauthorizedException {
                      if (!mounted) return false;
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(
                          builder: (context) => const LoginScreen(),
                        ),
                        (route) => false,
                      );
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text(
                            'Sesión expirada. Inicie sesión de nuevo.',
                          ),
                        ),
                      );
                      return false;
                    }
                  },
                  onDismissed: (direction) {
                    setState(() {
                      estaciones.removeAt(index);
                    });
                  },
                  child: Card(
                    margin: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 4,
                    ),
                    child: ListTile(
                      leading: FutureBuilder<Map<String, dynamic>>(
                        future: apiService.obtenerUltimaLectura(estacion.id),
                        builder: (context, snapshot) {
                          Color iconColor = Colors.blue; 

                          if (snapshot.connectionState ==
                              ConnectionState.done) {
                            if (snapshot.hasData && snapshot.data != null) {
                              final valor = snapshot.data!['valor'] ?? 0;

                              if (valor <= 70) {
                                iconColor = Colors.green;
                              } else {
                                iconColor = Colors.red;
                              }
                            } else if (snapshot.hasError) {
                              iconColor = Colors.blue;
                            }
                          }
                          return Icon(Icons.router, color: iconColor);
                        },
                      ),
                      title: Text(estacion.nombre),
                      subtitle: Text(estacion.ubicacion),
                      trailing: const Icon(Icons.edit, size: 20),
                      onTap: () => _mostrarDialogoEdicion(estacion),
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        child: const Icon(Icons.add),
        onPressed: () async {
          final bool? result = await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const AddEstacionScreen()),
          );
          if (result == true) {
            _cargarEstaciones();
          }
        },
      ),
    );
  }
}