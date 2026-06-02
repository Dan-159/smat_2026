import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/estacion.dart';
import 'auth_service.dart';

// Excepción personalizada para identificar token expirado o inválido
class UnauthorizedException implements Exception {
  final String message;
  UnauthorizedException([this.message = 'Sesión expirada']);
  @override
  String toString() => message;
}

class ApiService {
  final String baseUrl = "http://localhost:8000";
  final AuthService _authService = AuthService();

  // Obtener todas las estaciones 
  Future<List<Estacion>> obtenerEstaciones() async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/estaciones/'))
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final List jsonResponse = json.decode(response.body);
        return jsonResponse.map((data) => Estacion.fromJson(data)).toList();
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception(
        'No se pudo conectar con SMAT. ¿Está el servidor activo?',
      );
    }
  }

  // Crear una estación
  Future<bool> crearEstacion(int id, String nombre, String ubicacion) async {
    try {
      final token = await _authService.getToken();
      final response = await http.post(
        Uri.parse('$baseUrl/estaciones/'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'id': id, 'nombre': nombre, 'ubicacion': ubicacion}),
      );

      if (response.statusCode == 401) {
        await _authService.logout(); // Limpia el token expirado
        throw UnauthorizedException();
      }

      return response.statusCode == 200 || response.statusCode == 201;
    } on UnauthorizedException {
      rethrow; // Re-lanzamos para que la UI lo maneje
    } catch (_) {
      return false;
    }
  }

  // Eliminar una estación
  Future<bool> eliminarEstacion(int id) async {
    try {
      final token = await _authService.getToken();
      final response = await http.delete(
        Uri.parse('$baseUrl/estaciones/$id'),
        headers: {'Authorization': 'Bearer $token'},
      );

      if (response.statusCode == 401) {
        await _authService.logout();
        throw UnauthorizedException();
      }

      return response.statusCode == 204;
    } on UnauthorizedException {
      rethrow;
    } catch (_) {
      return false;
    }
  }

  // Editar una estación existente
  Future<bool> editarEstacion(int id, String nombre, String ubicacion) async {
    try {
      final token = await _authService.getToken();
      final response = await http.put(
        Uri.parse('$baseUrl/estaciones/$id'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode({'id': id, 'nombre': nombre, 'ubicacion': ubicacion}),
      );

      if (response.statusCode == 401) {
        await _authService.logout();
        throw UnauthorizedException();
      }

      return response.statusCode == 200;
    } on UnauthorizedException {
      rethrow;
    } catch (_) {
      return false;
    }
  }

  // Método para obtener la última lectura de una estación
  Future<Map<String, dynamic>> obtenerUltimaLectura(int estacionId) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/lecturas/$estacionId/ultima'))
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else if (response.statusCode == 404) {
        throw Exception('No hay lecturas de esta estación');
      } else {
        throw Exception('Error del servidor: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception(
        'No se pudo conectar con SMAT. ¿Está el servidor activo?',
      );
    }
  }
}